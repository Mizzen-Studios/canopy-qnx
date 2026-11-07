/* Original CANopy app; external public QNX headers only, no vendored ABI.
 * Native libcan fallback, NOT SocketCAN. Refuse a Linux stand-in build. */
#ifndef __QNXNTO__
#error This adapter requires the QNX target; host tests compile only portable sources
#endif
/* QNX extension declarations are hidden by strict ISO C without this. */
#ifndef _QNX_SOURCE
#define _QNX_SOURCE 1
#endif
#include "native_inputs.h"
#include <devctl.h>
#include <sys/can_dcmd.h>
#include <sys/neutrino.h>
#include <sys/syspage.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#define TICK_CODE _PULSE_CODE_MINAVAIL
static volatile sig_atomic_t quitting;
static void stop_signal(int sig) { (void)sig; quitting = 1; }
static uint64_t milliseconds(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t) == -1) { perror("clock_gettime"); exit(1); }
    return (uint64_t)t.tv_sec * 1000 + (uint64_t)t.tv_nsec / 1000000;
}
/* Bound even a wedged resource manager's SEND/REPLY, not just O_NONBLOCK.
 * QNX TimerTimeout is one-shot and must be armed before EVERY devctl. */
static int bounded_ctl(int fd, int cmd, struct can_msg *msg) {
    uint64_t ns = 2000000;
    if (TimerTimeout(CLOCK_MONOTONIC, _NTO_TIMEOUT_SEND | _NTO_TIMEOUT_REPLY,
                     NULL, &ns, NULL) == -1) return errno;
    return devctl(fd, cmd, msg, sizeof(*msg), NULL);
}
int main(int argc, char **argv) {
    int channel = -1, connection = -1, rx = -1, tx = -1, rc = 1;
    timer_t timer;
    int timer_created = 0;
    struct sched_param wanted = {0}, observed = {0};
    struct sigevent event;
    struct itimerspec period = {{0,10000000}, {0,10000000}};
    struct canopy_safestop stop;
    struct canopy_sensors sensors = {0};
    unsigned ticks = 0;
    uint64_t started_ms = 0;
    char *end;
    long cycles;
    const char *fault;
    uint8_t frozen[4] = {0};
    if (argc != 3) { fprintf(stderr,"usage: %s cycles(1..6000) none|bad-crc|frozen\n",argv[0]); return 2; }
    errno = 0; cycles = strtol(argv[1], &end, 10);
    if (errno || end == argv[1] || *end || cycles < 1 || cycles > 6000) return 2;
    fault = argv[2];
    if (strcmp(fault,"none") && strcmp(fault,"bad-crc") && strcmp(fault,"frozen")) return 2;
    setvbuf(stdout,NULL,_IONBF,0);
    wanted.sched_priority = 20;
    if (sched_setscheduler(0,SCHED_FIFO,&wanted) == -1 ||
        sched_getscheduler(0) != SCHED_FIFO || sched_getparam(0,&observed) == -1 ||
        observed.sched_priority != wanted.sched_priority) { perror("FIFO proof failed"); return 1; }
    printf("C6_FIFO policy=%d priority=%d pid=%ld transport=libcan-not-SocketCAN\n",
           sched_getscheduler(0), observed.sched_priority, (long)getpid());
    if (signal(SIGTERM,stop_signal) == SIG_ERR || signal(SIGINT,stop_signal) == SIG_ERR) goto done;
    canopy_safestop_init(&stop);
    channel = ChannelCreate(0);
    if (channel == -1) goto done;
    connection = ConnectAttach(0,0,channel,_NTO_SIDE_CHANNEL,0);
    if (connection == -1) goto done;
    SIGEV_PULSE_INIT(&event,connection,20,TICK_CODE,0);
    if (timer_create(CLOCK_MONOTONIC,&event,&timer) == -1) goto done;
    timer_created = 1;
    rx = open("/dev/can0/rx0",O_RDWR | O_NONBLOCK);
    tx = open("/dev/can0/tx0",O_RDWR | O_NONBLOCK);
    if (rx == -1 || tx == -1 || timer_settime(timer,0,&period,NULL) == -1) goto done;
    started_ms = milliseconds();
    puts("C6_READY timer=CLOCK_MONOTONIC interval_ns=10000000 rx=/dev/can0/rx0 exclusive-required");
    while (!quitting && ticks < (unsigned)cycles) {
        struct _pulse pulse;
        struct canopy_inputs in;
        struct canopy_heartbeat packet;
        struct can_msg msg;
        uint8_t bytes[4];
        uint64_t now;
        unsigned drained;
        int status;
        /* Bound receive too: a lost timer cannot leave this process hanging. */
        uint64_t receive_ns = 100000000;
        if (TimerTimeout(CLOCK_MONOTONIC,_NTO_TIMEOUT_RECEIVE,NULL,&receive_ns,NULL) == -1) goto done;
        if (MsgReceivePulse(channel,&pulse,sizeof(pulse),NULL) == -1) {
            if (errno == EINTR && quitting) break;
            goto done;
        }
        if (pulse.code != TICK_CODE) continue;
        now = milliseconds();
        if (now - started_ms >= 60000) { errno = ETIMEDOUT; goto done; }
        /* Up to four frames/tick, plus 2ms per IPC. No unlimited FIFO drain.
         * Discarded malformed known IDs invalidate freshness. */
        for (drained = 0; drained < 4; ++drained) {
            memset(&msg,0,sizeof(msg));
            status = bounded_ctl(rx,CAN_DEVCTL_RX_FRAME_RAW_NOBLOCK,&msg);
            if (status == EAGAIN) break;
            if (status != EOK) { errno = status; goto done; }
            /* dev-can-linux v1.12 netif_rx drops actual CAN_RTR_FLAG first,
             * then uses is_remote_frame=1 for non-echo DATA. This is a
             * deliberately fallback-specific adapter, not generic libcan.
             * Its timestamp uses ClockCycles/(cycles_per_sec/1e6)/1000,
             * NOT CLOCK_MONOTONIC epoch. Reject old/future queue contents. */
            {
                uint64_t per_us = SYSPAGE_ENTRY(qtime)->cycles_per_sec / 1000000;
                uint32_t driver_now, age;
                if (!per_us) goto done;
                driver_now = (uint32_t)(ClockCycles() / per_us / 1000);
                age = driver_now - msg.ext.timestamp;
                if (!msg.ext.is_extended_mid &&
                    !(msg.mid & ~((uint32_t)0x7ff << 18))) {
                    if (age <= 30 && now >= age)
                        (void)canopy_sensor_receive(&sensors,now-age,msg.mid >> 18,msg.dat,msg.len);
                    else
                        (void)canopy_sensor_receive(&sensors,now,msg.mid >> 18,NULL,0);
                }
            }
        }
        if (drained == 4) {
            /* A full budget may hide a stale backlog: never drive from it. */
            sensors.speed_seen = sensors.obstacle_seen = false;
        }
        now = milliseconds();
        in = canopy_sensor_snapshot(&sensors,now);
        if (!canopy_safestop_cycle(&stop,now,&in,&packet) ||
            !canopy_heartbeat_encode(&packet,bytes)) goto done;
        /* Explicit test-only fault begins AFTER 200 normal cycles. */
        if (ticks == 199) memcpy(frozen,bytes,4);
        if (ticks >= 200 && !strcmp(fault,"bad-crc")) bytes[3] ^= 1;
        if (ticks >= 200 && !strcmp(fault,"frozen")) memcpy(bytes,frozen,4);
        memset(&msg,0,sizeof(msg));
        msg.mid = CANOPY_HEARTBEAT_ID << 18; msg.len = 4;
        memcpy(msg.dat,bytes,4);
        status = bounded_ctl(tx,CAN_DEVCTL_TX_FRAME_RAW,&msg);
        if (status != EOK) { errno = status; goto done; }
        printf("C6_TICK n=%u ms=%" PRIu64 " state=%u brake=%u counter=%u latched=%u fresh=%u speed_age=%" PRId64 " obstacle_age=%" PRId64 " payload=%02x%02x%02x%02x fault=%s\n",
            ticks,now,packet.state,packet.brake,packet.counter,stop.latched,stop.fresh_cycles,
            in.speed_age_ms,in.obstacle_age_ms,bytes[0],bytes[1],bytes[2],bytes[3],ticks >= 200 ? fault : "none");
        ++ticks;
    }
    rc = 0;
done:
    if (rc) perror("C6_FAIL_CLOSED exiting; host ECU must assert its independent deadline");
    if (timer_created) timer_delete(timer);
    if (rx != -1) close(rx);
    if (tx != -1) close(tx);
    if (connection != -1) ConnectDetach(connection);
    if (channel != -1) ChannelDestroy(channel);
    printf("C6_EXIT ticks=%u rc=%d signal=%d\n",ticks,rc,(int)quitting);
    return rc;
}
