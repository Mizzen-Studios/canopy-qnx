/* HOST SIM parity harness, not a target process or QPP integration. */
#include <stdio.h>
#include <inttypes.h>
#include "pilot_model.h"
int main(void) {
    int32_t x[3];
    while (scanf("%" SCNd32 " %" SCNd32 " %" SCNd32, &x[0], &x[1], &x[2]) == 3) {
        canopy_pilot_request r = canopy_pilot_infer(x);
        printf("%d %" PRId32 " %" PRId32 "%c", canopy_pilot_action(x), r.speed_mps, r.steering_deg, 10);
    }
    return ferror(stdin) ? 1 : 0;
}
