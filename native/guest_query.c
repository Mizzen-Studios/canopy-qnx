/* Bounded snapshot queries, not a continuous monitor or safety mechanism. */
#include <sys/neutrino.h>
#include <sys/iomsg.h>
#include <sys/netmgr.h>
#include <sys/stat.h>
#include <stdint.h>
#include <signal.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <limits.h>
#define ENDPOINT "/tmp/canopy-query.endpoint"
#define MAGIC 0x43515931
struct request { int magic, op; pid_t replacement; };
struct response { int magic, killed, recovery, survivor; pid_t server, target, replacement, mainpid; };
static int number(const char *s) { char *e; errno=0; long v=strtol(s,&e,10); return errno||*e||v<2||v>INT_MAX?-1:(int)v; }
static int alive(pid_t p) { return p>1 && kill(p,0)==0; }
static int absent(pid_t p) { errno=0; return kill(p,0)<0 && errno==ESRCH; }
int main(int argc,char **argv) {
 setvbuf(stdout,NULL,_IONBF,0);umask(0077);
 if(argc==4&&!strcmp(argv[1],"serve")) {
  pid_t target=number(argv[2]), mainpid=number(argv[3]), replacement=0;
  if(target<2||mainpid<2||target==mainpid||!alive(target)||!alive(mainpid))return 2;
  int chid=ChannelCreate(0); if(chid<0)return 3;
  FILE *f=fopen(ENDPOINT,"wx"); if(!f){ChannelDestroy(chid);return 4;}
  fprintf(f,"%ld %d\n",(long)getpid(),chid);fclose(f);
  printf("CANOPY_QUERY_READY pid=%ld chid=%d target=%ld main=%ld\n",(long)getpid(),chid,(long)target,(long)mainpid);
  for(;;){struct request m={0};struct _msg_info info;int rcvid=MsgReceive(chid,&m,sizeof m,&info);
   if(rcvid<0){if(errno==EINTR)continue;break;}if(!rcvid)continue;
   if(info.msglen!=(int)sizeof m||m.magic!=MAGIC||m.op<0||m.op>6){MsgError(rcvid,EINVAL);continue;}
   if(m.op==1){if(replacement||m.replacement<2||m.replacement==target||m.replacement==mainpid||!absent(target)||!alive(m.replacement)||!alive(mainpid)){MsgError(rcvid,EINVAL);continue;}replacement=m.replacement;}
   struct response r={MAGIC,absent(target),replacement>1&&replacement!=target&&alive(replacement),alive(mainpid),getpid(),target,replacement,mainpid};
   MsgReply(rcvid,EOK,&r,sizeof r);if(m.op==5)break;
  }
  unlink(ENDPOINT);ChannelDestroy(chid);return 0;
 }
 int op=-1;pid_t replacement=0;
 if(argc==3&&!strcmp(argv[1],"publish")){op=1;replacement=number(argv[2]);if(replacement<2)return 2;}
 if(argc==2){if(!strcmp(argv[1],"killed"))op=2;else if(!strcmp(argv[1],"recovery"))op=3;else if(!strcmp(argv[1],"survivors"))op=4;else if(!strcmp(argv[1],"stop"))op=5;else if(!strcmp(argv[1],"isolation"))op=6;}
 if(op<0)return 2;
 long server;int chid;FILE*f=fopen(ENDPOINT,"r");if(!f)return 6;
 int parsed=fscanf(f,"%ld %d",&server,&chid);fclose(f);if(parsed!=2||server<2||server>INT_MAX||chid<0)return 7;
 int coid=ConnectAttach(ND_LOCAL_NODE,(pid_t)server,chid,_NTO_SIDE_CHANNEL,0);if(coid<0)return 8;
 struct request m={MAGIC,op,replacement};struct response r={0};uint64_t timeout=5000000000ULL;TimerTimeout(CLOCK_MONOTONIC,_NTO_TIMEOUT_SEND|_NTO_TIMEOUT_REPLY,NULL,&timeout,NULL);int rc=MsgSend(coid,&m,sizeof m,&r,sizeof r);ConnectDetach(coid);
 if(rc<0||r.magic!=MAGIC||r.server!=server)return 9;
 const char*q=op==1?"publish":op==2?"killed":op==3?"recovery":op==4?"survivors":op==5?"stop":"isolation";
 printf("CANOPY_GUEST_QUERY {\"schema\":\"canopy-query-1\",\"query\":\"%s\",\"server\":%ld,\"target\":%ld,\"replacement\":%ld,\"main\":%ld,\"killed\":%d,\"recovery\":%d,\"survivor\":%d}\n",q,(long)r.server,(long)r.target,(long)r.replacement,(long)r.mainpid,r.killed,r.recovery,r.survivor);
 /* Only bounded process snapshots. Traffic/control and SLM origin remain separately bound. */
 return 0;
}
