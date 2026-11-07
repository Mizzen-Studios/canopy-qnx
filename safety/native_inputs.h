/* Original application boundary, no QNX ABI declarations. */
#ifndef CANOPY_NATIVE_INPUTS_H
#define CANOPY_NATIVE_INPUTS_H
#include "safestop.h"
struct canopy_sensors {
    bool speed_seen, obstacle_seen;
    uint64_t speed_ms, obstacle_ms;
    double speed_mps, obstacle_m;
};
/* Existing demo VSS IDs: 100 LE speed .01 km/h, 102 BE distance .01 m.
 * Unknown IDs ignored; malformed known frames invalidate that sensor. */
bool canopy_sensor_receive(struct canopy_sensors *, uint64_t, uint32_t,
                           const uint8_t *, size_t);
struct canopy_inputs canopy_sensor_snapshot(const struct canopy_sensors *, uint64_t);
#endif
