/*
 * Copyright (c) 2003-2006 The Regents of The University of Michigan
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __GEM5_M5OP_H__
#define __GEM5_M5OP_H__

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

#ifndef __GEM5_ASM_GENERIC_M5OPS_H__
#define __GEM5_ASM_GENERIC_M5OPS_H__

#define M5OP_ARM                0x00
#define M5OP_QUIESCE            0x01
#define M5OP_QUIESCE_NS         0x02
#define M5OP_QUIESCE_CYCLE      0x03
#define M5OP_QUIESCE_TIME       0x04
#define M5OP_RPNS               0x07
#define M5OP_WAKE_CPU           0x09
#define M5OP_DEPRECATED1        0x10 // obsolete ivlb
#define M5OP_DEPRECATED2        0x11 // obsolete ivle
#define M5OP_DEPRECATED3        0x20 // deprecated exit function
#define M5OP_EXIT               0x21
#define M5OP_FAIL               0x22
#define M5OP_SUM                0x23 // For testing
#define M5OP_INIT_PARAM         0x30
#define M5OP_LOAD_SYMBOL        0x31
#define M5OP_RESET_STATS        0x40
#define M5OP_DUMP_STATS         0x41
#define M5OP_DUMP_RESET_STATS   0x42
#define M5OP_CHECKPOINT         0x43
#define M5OP_WRITE_FILE         0x4F
#define M5OP_READ_FILE          0x50
#define M5OP_DEBUG_BREAK        0x51
#define M5OP_SWITCH_CPU         0x52
#define M5OP_ADD_SYMBOL         0x53
#define M5OP_PANIC              0x54

#define M5OP_RESERVED1          0x55 // Reserved for user, used to be annotate
#define M5OP_RESERVED2          0x56 // Reserved for user
#define M5OP_RESERVED3          0x57 // Reserved for user
#define M5OP_RESERVED4          0x58 // Reserved for user
#define M5OP_RESERVED5          0x59 // Reserved for user

#define M5OP_WORK_BEGIN         0x5a
#define M5OP_WORK_END           0x5b

#define M5OP_DIST_TOGGLE_SYNC   0x62

#define M5OP_WORKLOAD           0x70


#define M5OP_FOREACH                                            \
    M5OP(m5_arm, M5OP_ARM)                                      \
    M5OP(m5_quiesce, M5OP_QUIESCE)                              \
    M5OP(m5_quiesce_ns, M5OP_QUIESCE_NS)                        \
    M5OP(m5_quiesce_cycle, M5OP_QUIESCE_CYCLE)                  \
    M5OP(m5_quiesce_time, M5OP_QUIESCE_TIME)                    \
    M5OP(m5_rpns, M5OP_RPNS)                                    \
    M5OP(m5_wake_cpu, M5OP_WAKE_CPU)                            \
    M5OP(m5_exit, M5OP_EXIT)                                    \
    M5OP(m5_fail, M5OP_FAIL)                                    \
    M5OP(m5_sum, M5OP_SUM)                                      \
    M5OP(m5_init_param, M5OP_INIT_PARAM)                        \
    M5OP(m5_load_symbol, M5OP_LOAD_SYMBOL)                      \
    M5OP(m5_reset_stats, M5OP_RESET_STATS)                      \
    M5OP(m5_dump_stats, M5OP_DUMP_STATS)                        \
    M5OP(m5_dump_reset_stats, M5OP_DUMP_RESET_STATS)            \
    M5OP(m5_checkpoint, M5OP_CHECKPOINT)                        \
    M5OP(m5_write_file, M5OP_WRITE_FILE)                        \
    M5OP(m5_read_file, M5OP_READ_FILE)                          \
    M5OP(m5_debug_break, M5OP_DEBUG_BREAK)                      \
    M5OP(m5_switch_cpu, M5OP_SWITCH_CPU)                        \
    M5OP(m5_add_symbol, M5OP_ADD_SYMBOL)                        \
    M5OP(m5_panic, M5OP_PANIC)                                  \
    M5OP(m5_work_begin, M5OP_WORK_BEGIN)                        \
    M5OP(m5_work_end, M5OP_WORK_END)                            \
    M5OP(m5_dist_toggle_sync, M5OP_DIST_TOGGLE_SYNC)            \
    M5OP(m5_workload, M5OP_WORKLOAD)                            \

#define M5OP_MERGE_TOKENS_I(a, b) a##b
#define M5OP_MERGE_TOKENS(a, b) M5OP_MERGE_TOKENS_I(a, b)

#endif //  __GEM5_ASM_GENERIC_M5OPS_H__

void m5_arm(uint64_t address);
void m5_quiesce(void);
void m5_quiesce_ns(uint64_t ns);
void m5_quiesce_cycle(uint64_t cycles);
uint64_t m5_quiesce_time(void);
uint64_t m5_rpns();
void m5_wake_cpu(uint64_t cpuid);

void m5_exit(uint64_t ns_delay);
void m5_fail(uint64_t ns_delay, uint64_t code);
// m5_sum is for sanity checking the gem5 op interface.
unsigned m5_sum(unsigned a, unsigned b, unsigned c,
                unsigned d, unsigned e, unsigned f);
uint64_t m5_init_param(uint64_t key_str1, uint64_t key_str2);
void m5_checkpoint(uint64_t ns_delay, uint64_t ns_period);
void m5_reset_stats(uint64_t ns_delay, uint64_t ns_period);
void m5_dump_stats(uint64_t ns_delay, uint64_t ns_period);
void m5_dump_reset_stats(uint64_t ns_delay, uint64_t ns_period);
uint64_t m5_read_file(void *buffer, uint64_t len, uint64_t offset);
uint64_t m5_write_file(void *buffer, uint64_t len, uint64_t offset,
                       const char *filename);
void m5_debug_break(void);
void m5_switch_cpu(void);
void m5_dist_toggle_sync(void);
void m5_add_symbol(uint64_t addr, const char *symbol);
void m5_load_symbol();
void m5_panic(void);
void m5_work_begin(uint64_t workid, uint64_t threadid);
void m5_work_end(uint64_t workid, uint64_t threadid);

/*
 * Send a very generic poke to the workload so it can do something. It's up to
 * the workload to know what information to look for to interpret an event,
 * such as what PC it came from, what register values are, or the context of
 * the workload itself (is this SE mode? which OS is running?).
 */
void m5_workload();

/*
 * Create _addr and _semi versions all declarations, e.g. m5_exit_addr and
 * m5_exit_semi. These expose the the memory and semihosting variants of the
 * ops.
 *
 * Some of those declarations are not defined for certain ISAs, e.g. X86
 * does not have _semi, but we felt that ifdefing them out could cause more
 * trouble tham leaving them in.
 */
#define M5OP(name, func) __typeof__(name) M5OP_MERGE_TOKENS(name, _addr); \
                         __typeof__(name) M5OP_MERGE_TOKENS(name, _semi);
M5OP_FOREACH
#undef M5OP

#ifdef __cplusplus
}
#endif
#endif // __GEM5_M5OP_H__
