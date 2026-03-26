#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

/* This prevents the macOS security macro from mangling the fio headers */
#ifdef strlcat
#undef strlcat
#endif
#ifdef strlcpy
#undef strlcpy
#endif

#include "fio.h"

struct my_proto_data {
    unsigned long long count;
};

/**
 * This is where custom protocol logic would be
 */
static enum fio_q_status cb_queue(struct thread_data *td, struct io_u *io_u) {
    struct my_proto_data *pd = td->io_ops_data;
    if (pd) {
        pd->count++;
    }
    
    // THIS IS THE CRITICAL ADDITION!
    // Simulate 50 microseconds of network latency to prevent CPU/math overflows.
    usleep(50); 
    
    io_u->error = 0; 
    
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
    if (pd) {
        // We removed the printf so we don't corrupt the JSON stream going to Python!
        free(pd);
        // CRITICAL: Nullify the pointer to prevent FIO from double-freeing during multi-thread teardown
        td->io_ops_data = NULL; 
    }
}

/* * Dummy open/close functions required by FIO 
 * Even with FIO_DISKLESSIO, the engine core still attempts to "open" the target
 */
static int cb_open_file(struct thread_data *td, struct fio_file *f) {
    f->fd = open("/dev/null", O_RDWR);
    return 0; // Return 0 for success
}

static int cb_close_file(struct thread_data *td, struct fio_file *f) {
    if (f->fd != -1) {
        close(f->fd);
        f->fd = -1;
    }
    return 0; // Return 0 for success
}

static struct ioengine_ops ioengine = {
    .name           = "my_protocol",
    .version        = FIO_IOOPS_VERSION,
    .queue          = cb_queue,
    .init           = cb_init,
    .cleanup        = cb_cleanup,
    .open_file      = cb_open_file,    // <-- Hook added
    .close_file     = cb_close_file,   // <-- Hook added
    // FIO_SYNCIO: Handled synchronously
    // FIO_DISKLESSIO: Essential to ignore that "127.0.0.1" isn't a real file
    // FIO_NOEXTEND: Prevents fio from trying to 'truncate' or 'extend' the target
    .flags          = FIO_SYNCIO | FIO_DISKLESSIO | FIO_NOEXTEND,
};

/**
 * Avoids linker/loader errors
 */
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