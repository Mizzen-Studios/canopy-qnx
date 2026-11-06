/* Original portable demo logic; no SDK dependencies or safety certification. */
#ifndef CANOPY_SAFESTOP_H
#define CANOPY_SAFESTOP_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define CANOPY_HEARTBEAT_ID 0x200u
struct canopy_inputs {
    int64_t speed_age_ms, obstacle_age_ms;
    double obstacle_m, pilot_speed_mps;
};
enum canopy_state { CANOPY_DRIVE, CANOPY_BRAKE, CANOPY_SAFE_STOP, CANOPY_RECOVER };
struct canopy_heartbeat { unsigned state, brake, counter; };
struct canopy_safestop {
    bool latched, has_time;
    unsigned fresh_cycles, brake, counter;
    uint64_t last_ms;
};
void canopy_safestop_init(struct canopy_safestop *stop);
/* Invalid/nonincreasing time returns false without changing state or output. */
bool canopy_safestop_cycle(struct canopy_safestop *stop, uint64_t now_ms,
                          const struct canopy_inputs *inputs,
                          struct canopy_heartbeat *out);
uint8_t canopy_crc8(const uint8_t *data, size_t size);
bool canopy_heartbeat_encode(const struct canopy_heartbeat *packet, uint8_t out[4]);
bool canopy_heartbeat_decode(uint32_t id, const uint8_t *data, size_t size,
                             struct canopy_heartbeat *out);
#endif
