#include <sys/slog2.h>
#include <stdio.h>
#include <unistd.h>
/* Three finite structured records, one 4 KiB buffer, bounded retries. */
int main(void){slog2_buffer_set_config_t c={0};slog2_buffer_t h;
 c.num_buffers=1;c.buffer_set_name="canopy_prereq";c.verbosity_level=SLOG2_INFO;
 c.buffer_config[0].buffer_name="events";c.buffer_config[0].num_pages=1;c.max_retries=3;
 if(slog2_register(&c,&h,SLOG2_LIMIT_RETRIES)){perror("slog2_register");return 1;}
 for(int i=0;i<3;i++)if(slog2f(h,410+i,SLOG2_INFO,"{\"schema\":\"canopy-prereq-v1\",\"sequence\":%d,\"event\":\"bounded_probe\"}",i)){perror("slog2f");return 2;}
 puts("SLOG_PRODUCER records=3 pages=1 retries=3");return 0;}
