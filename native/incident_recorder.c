/* Bounded separate QNX observer. Serial JSON duplicates slog2 for loss checks. */
#include <sys/slog2.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static slog2_buffer_t h; static unsigned seq; static struct timespec start;
static unsigned long ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (t.tv_sec-start.tv_sec)*1000+(t.tv_nsec-start.tv_nsec)/1000000;}
static int event(const char *phase,long pid,int result){char b[512];snprintf(b,sizeof b,"{\"schema\":\"canopy-native-1\",\"seq\":%u,\"ms\":%lu,\"recorder\":%ld,\"phase\":\"%s\",\"pid\":%ld,\"result\":%d}",seq++,ms(),(long)getpid(),phase,pid,result);puts(b);return slog2c(h,500+seq,SLOG2_INFO,b);}
int main(int argc,char **argv){
 if(argc!=2)return 2;char *end;long target=strtol(argv[1],&end,10);if(*end||target<2)return 2;
 setvbuf(stdout,NULL,_IONBF,0);clock_gettime(CLOCK_MONOTONIC,&start);
 slog2_buffer_set_config_t c={0};c.num_buffers=1;c.buffer_set_name="canopy_incident";c.verbosity_level=SLOG2_INFO;c.buffer_config[0].buffer_name="incident";c.buffer_config[0].num_pages=1;c.max_retries=3;
 if(slog2_register(&c,&h,SLOG2_LIMIT_RETRIES))return 3;
 if(event("before",target,kill(target,0)))return 4;
 errno=0;int rc=kill(target,SIGKILL);if(event("kill",target,rc?errno:0)||rc)return 5;
 /* Target is SLM's child, not ours: waitpid ECHILD must remain explicit. */
 int status=0;errno=0;rc=waitpid(target,&status,WNOHANG);if(event("waitpid",target,rc<0?errno:rc))return 6;
 int absent=0;for(int i=0;i<100;i++){errno=0;if(kill(target,0)<0&&errno==ESRCH){absent=1;break;}usleep(20000);}
 if(event("interruption",target,absent))return 7;
 if(event("after",target,0))return 8;
 return absent?0:9;
}
