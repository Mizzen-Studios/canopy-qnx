/* HOST SIM learned model; no QNX runtime validation. */
#ifndef CANOPY_PILOT_MODEL_H
#define CANOPY_PILOT_MODEL_H
#include <stdint.h>
typedef struct { int32_t feature, threshold, left, right, action; } canopy_pilot_node;
static const canopy_pilot_node canopy_pilot_nodes[] = {
    {0, 2999, 1, 4, 3},
    {0, 1195, 2, 3, 1},
    {-1, 0, -1, -1, 0},
    {-1, 0, -1, -1, 1},
    {2, -4986, 5, 6, 3},
    {-1, 0, -1, -1, 3},
    {2, 4889, 7, 8, 4},
    {-1, 0, -1, -1, 2},
    {-1, 0, -1, -1, 4},
};
typedef struct { int32_t speed_mps, steering_deg; } canopy_pilot_request;
static const canopy_pilot_request canopy_pilot_actions[] = {
    {0, 0},
    {4, 0},
    {12, 0},
    {8, -10},
    {8, 10},
};
static inline int canopy_pilot_action(const int32_t features[3]) {
    int i = 0;
    while (canopy_pilot_nodes[i].feature >= 0) {
        const canopy_pilot_node *n = &canopy_pilot_nodes[i];
        i = features[n->feature] <= n->threshold ? n->left : n->right;
    }
    return canopy_pilot_nodes[i].action;
}
static inline canopy_pilot_request canopy_pilot_infer(const int32_t features[3]) {
    return canopy_pilot_actions[canopy_pilot_action(features)];
}
#endif
