#include <string.h>  // Force system strings to load first
#include <stdlib.h>
#include <stdio.h>

/* This prevents the macOS security macro from mangling the fio headers */
#ifdef strlcat
#undef strlcat
#endif
#ifdef strlcpy
#undef strlcpy
#endif

#include "fio.h"     // Now include the fio headers

struct my_proto_data {
    unsigned long long count;
};

// This is where you'd put your protocol-specific logic
static enum fio_q_status cb_queue(struct thread_data *td, struct io_u *io_u) {
    struct my_proto_data *pd = td->io_ops_data;
    pd->count++;
    
    // Simulate a successful protocol "send"
    return FIO_Q_COMPLETED; 
}

static int cb_init(struct thread_data *td) {
    struct my_proto_data *pd = malloc(sizeof(*pd));
    pd->count = 0;
    td->io_ops_data = pd;
    return 0;
}

static void cb_cleanup(struct thread_data *td) {
    struct my_proto_data *pd = td->io_ops_data;
    printf("Custom Protocol Handled %llu IOs\n", pd->count);
    free(pd);
}

static struct ioengine_ops ioengine = {
    .name           = "my_protocol",
    .version        = FIO_IOOPS_VERSION,
    .queue          = cb_queue,
    .init           = cb_init,
    .cleanup        = cb_cleanup,
    // FIO_SYNCIO: Handled synchronously (simple)
    // FIO_DISKLESSIO: Essential to ignore that "127.0.0.1" isn't a real file
    // FIO_NOEXTEND: Prevents fio from trying to 'truncate' or 'extend' the target
    .flags          = FIO_SYNCIO | FIO_DISKLESSIO | FIO_NOEXTEND,
};


// Avoids linker/loader errors
static void fio_init my_proto_register(void) {
    register_ioengine(&ioengine);
}
static void fio_exit my_proto_unregister(void) {
    unregister_ioengine(&ioengine);
}

__attribute__((visibility("default")))
void get_ioengine(struct ioengine_ops **ioengine_ptr) {
    *ioengine_ptr = &ioengine;
}