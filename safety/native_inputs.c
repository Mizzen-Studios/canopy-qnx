#include "native_inputs.h"
#include <limits.h>
bool canopy_sensor_receive(struct canopy_sensors *s, uint64_t now, uint32_t id,
                           const uint8_t *data, size_t size)
{
    unsigned raw;
    if (!s || (id != 0x100 && id != 0x102)) return false;
    if (!data || size != 2) {
        if (id == 0x100) s->speed_seen = false;
        else s->obstacle_seen = false;
        return false;
    }
    raw = id == 0x100 ? data[0] + 256u * data[1] : 256u * data[0] + data[1];
    if (id == 0x100) {
        s->speed_seen = raw <= 25000;
        s->speed_ms = now;
        s->speed_mps = raw / 360.0;
        return s->speed_seen;
    }
    s->obstacle_seen = raw <= 50000;
    s->obstacle_ms = now;
    s->obstacle_m = raw / 100.0;
    return s->obstacle_seen;
}
static int64_t age(bool seen, uint64_t stamp, uint64_t now)
{
    return !seen || now < stamp || now - stamp > INT64_MAX ? -1 : (int64_t)(now - stamp);
}
struct canopy_inputs canopy_sensor_snapshot(const struct canopy_sensors *s, uint64_t now)
{
    return (struct canopy_inputs){age(s->speed_seen, s->speed_ms, now),
        age(s->obstacle_seen, s->obstacle_ms, now), s->obstacle_m, s->speed_mps};
}
