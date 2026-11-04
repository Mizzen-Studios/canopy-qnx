#include <pthread.h>
#include <unistd.h>
#include <sys/wait.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
extern char **environ;
static void *worker(void *argument) { return argument; }
int main(void) {
 pthread_t thread; void *result = NULL;
 if (pthread_create(&thread, NULL, worker, (void*)42) || pthread_join(thread, &result) || result != (void*)42) return 1;
 pid_t child=fork(); if (child<0) return 2; if (!child) _exit(17);
 int status; if (waitpid(child,&status,0)!=child || !WIFEXITED(status) || WEXITSTATUS(status)!=17) return 3;
 char *args[]={"true",NULL}; if(posix_spawn(&child,"/usr/bin/true",NULL,NULL,args,environ) || waitpid(child,&status,0)!=child || status) return 4;
 void *library=dlopen("libm.so.6",RTLD_NOW); if(!library) return 5;
 double (*function)(double)=dlsym(library,"cos"); if(!function || function(0.0)!=1.0) return 6;
 dlclose(library); puts("PASS x86_64 glibc pthread/fork/wait/posix_spawn/dlopen"); return 0;
}
