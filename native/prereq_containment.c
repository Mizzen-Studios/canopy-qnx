#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
/* Finite negative control; no CAN or safety logic. */
static void *observer(void *unused){(void)unused;for(int i=0;i<3;i++){printf("COLOCATED sample=%d pid=%ld\n",i,(long)getpid());usleep(100000);}puts("COLOCATED_READY");for(;;)pause();return NULL;}
int main(int argc,char **argv){
 setvbuf(stdout,NULL,_IONBF,0);
 if(argc==2 && !strcmp(argv[1],"worker")){pthread_t t;if(pthread_create(&t,NULL,observer,NULL))return 2;pthread_join(t,NULL);return 3;}
 int fd[2];if(pipe(fd))return 4;pid_t p=fork();if(p<0)return 5;
 if(!p){dup2(fd[1],1);close(fd[0]);close(fd[1]);execl(argv[0],argv[0],"worker",(char*)NULL);_exit(6);}
 close(fd[1]);FILE *f=fdopen(fd[0],"r");char line[256];int ready=0;
 while(fgets(line,sizeof line,f)){printf("RECORDER captured=%s",line);if(strstr(line,"COLOCATED_READY")){ready=1;break;}}
 if(!ready){kill(p,SIGKILL);waitpid(p,NULL,0);return 7;}
 printf("SEPARATE_RECORDER before_kill pid=%ld target=%ld\n",(long)getpid(),(long)p);if(kill(p,SIGKILL))return 8;
 int status;if(waitpid(p,&status,0)!=p)return 9;int post=0;while(fgets(line,sizeof line,f))post++;int eof=feof(f);fclose(f);
 printf("NEGATIVE_CONTROL signal=%d eof=%d colocated_post_kill=%d\n",WIFSIGNALED(status)?WTERMSIG(status):0,eof,post);
 for(int i=0;i<3;i++){printf("SEPARATE_RECORDER after_kill=%d pid=%ld\n",i,(long)getpid());usleep(100000);}
 return !(WIFSIGNALED(status)&&WTERMSIG(status)==SIGKILL&&eof&&post==0);
}
