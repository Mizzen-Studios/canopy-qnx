/* Original CANopy application. No SDK or upstream implementation is vendored. */
#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <net/if.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>
#ifdef __QNXNTO__
#include <hw/socketcan.h>
#else
#include <linux/can.h>
#include <linux/can/raw.h>
#endif

static int64_t milliseconds(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC,&t)<0) return -1;
    return (int64_t)t.tv_sec*1000+t.tv_nsec/1000000;
}
int main(int argc, char **argv) {
    if (argc!=4 || (strcmp(argv[1],"tx") && strcmp(argv[1],"rx"))) {
        fprintf(stderr,"usage: %s tx|rx interface count(1..1000)\n",argv[0]);
        return 2;
    }
    char *end; errno=0;
    long requested=strtol(argv[3],&end,10);
    if (errno || end==argv[3] || *end || requested<1 || requested>1000) return 2;
    int tx=!strcmp(argv[1],"tx");
    unsigned index=if_nametoindex(argv[2]);
    if (!index) { perror("if_nametoindex"); return 1; }
    int fd=socket(PF_CAN,SOCK_RAW,CAN_RAW);
    if (fd<0) { perror("socket(PF_CAN)"); return 1; }
    int rc=1, observed=0;
    int flags=fcntl(fd,F_GETFL,0);
    if (flags<0 || fcntl(fd,F_SETFL,flags|O_NONBLOCK)<0) { perror("fcntl"); goto done; }
    struct sockaddr_can addr={0}; addr.can_family=AF_CAN; addr.can_ifindex=(int)index;
    if (bind(fd,(struct sockaddr *)&addr,sizeof(addr))<0) { perror("bind"); goto done; }
    const uint8_t incoming[8]={1,2,3,4,5,6,7,8};
    const uint8_t outgoing[8]={0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88};
    if (!tx) {
        struct can_filter filter={0};
        filter.can_id=0x123;
        /* CAN_ERR_FLAG in the mask selects the error subscription on Linux.
         * Keep default error mask zero; filter only standard non-RTR data. */
        filter.can_mask=CAN_SFF_MASK|CAN_EFF_FLAG|CAN_RTR_FLAG;
        if (setsockopt(fd,SOL_CAN_RAW,CAN_RAW_FILTER,&filter,sizeof(filter))<0) {
            perror("CAN_RAW_FILTER"); goto done;
        }
    }
    setvbuf(stdout,NULL,_IONBF,0);
    printf("SOCKETCAN_%s_READY interface=%s requested=%ld\n",tx?"TX":"RX",argv[2],requested);
    int64_t start=milliseconds();
    if (start<0) { perror("clock_gettime"); goto done; }
    int64_t deadline=start+10000+requested*30;
    while (observed<requested) {
        int64_t now=milliseconds();
        if (now<0 || now>=deadline) { fputs("deadline exceeded\n",stderr); goto done; }
        struct pollfd ready={fd,tx?POLLOUT:POLLIN,0};
        int timeout=(int)(deadline-now);
        int status=poll(&ready,1,timeout);
        if (status<0 && errno==EINTR) continue;
        if (status<0) { perror("poll"); goto done; }
        if (!status) continue;
        if (ready.revents&(POLLERR|POLLHUP|POLLNVAL)) { fputs("socket poll error\n",stderr); goto done; }
        struct can_frame frame={0};
        ssize_t n;
        if (tx) {
            frame.can_id=0x321; frame.can_dlc=8;
            memcpy(frame.data,outgoing,8);
            n=write(fd,&frame,sizeof(frame));
        } else n=read(fd,&frame,sizeof(frame));
        if (n<0 && (errno==EAGAIN || errno==EWOULDBLOCK || errno==EINTR)) continue;
        if (n!=(ssize_t)sizeof(frame)) { fputs("incomplete CAN frame I/O\n",stderr); goto done; }
        if (!tx && (frame.can_id!=0x123 || frame.can_dlc!=8 || memcmp(frame.data,incoming,8))) {
            fputs("RX payload mismatch\n",stderr); goto done;
        }
        observed++;
        if (tx) {
            struct timespec pause={0,30000000};
            while (nanosleep(&pause,&pause)<0) {
                if (errno!=EINTR) { perror("nanosleep"); goto done; }
            }
        }
    }
    rc=0;
done:
    printf("SOCKETCAN_%s observed=%d/%ld result=%s\n",tx?"TX_ACCEPTED":"RX_EXACT",observed,requested,rc?"FAIL":"PASS");
    close(fd);
    return rc;
}
