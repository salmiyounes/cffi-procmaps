from cffi import FFI

ffi = FFI()

ffi.set_source(
    'pcmffi._pcmffi', '#include "pmparser.h"',
    include_dirs=["src"],
    sources=["src/pmparser.c"]
)

ffi.cdef("""\
        typedef enum
        {
            PROCMAPS_MAP_FILE,
            PROCMAPS_MAP_STACK,
            PROCMAPS_MAP_STACK_TID,
            PROCMAPS_MAP_VDSO,
            PROCMAPS_MAP_VVAR,
            PROCMAPS_MAP_VSYSCALL,
            PROCMAPS_MAP_HEAP,
            PROCMAPS_MAP_ANON_PRIV,
            PROCMAPS_MAP_ANON_SHMEM,
            PROCMAPS_MAP_ANON_MMAPS,
            PROCMAPS_MAP_OTHER,
        } procmaps_map_type;

        typedef struct procmaps_struct
        {
            void *addr_start; //< start address of the area
            void *addr_end;	  //< end address
            size_t length;	  //< size of the range
            short is_r;
            short is_w;
            short is_x;
            short is_p;
            size_t offset; //< offset
            unsigned int dev_major;
            unsigned int dev_minor;
            unsigned long long inode; //< inode of the file that backs the area
            char *pathname;			  //< the path of the file that backs the area ( dynamically allocated)
            procmaps_map_type map_type;
            char map_anon_name[81]; //< name of the anonymous mapping in case map_type is an anon mapping
            short file_deleted;								   //< whether the file backing the mapping was deleted
            // chained list
            struct procmaps_struct *next; //<handler of the chained list
        } procmaps_struct;

        typedef enum procmaps_error
        {
            PROCMAPS_SUCCESS = 0,
            PROCMAPS_ERROR_OPEN_MAPS_FILE,
            PROCMAPS_ERROR_READ_MAPS_FILE,
            PROCMAPS_ERROR_MALLOC_FAIL,
        } procmaps_error_t;

        typedef struct procmaps_iterator
        {
            procmaps_struct *head;
            procmaps_struct *current;
            size_t count;
        } procmaps_iterator;

        procmaps_error_t pmparser_parse(int pid, procmaps_iterator *maps_it);

        procmaps_struct *pmparser_next(procmaps_iterator *p_procmaps_it);

        void pmparser_free(procmaps_iterator *p_procmaps_it);
""")

if __name__ == "__main__":
    ffi.compile(verbose=True)