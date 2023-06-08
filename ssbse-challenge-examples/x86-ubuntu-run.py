# Copyright (c) 2023 The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

This script shows an example of running a full system Ubuntu boot simulation
using the gem5 standard library. This simulation boots Ubuntu 18.04 using 2
TIMING CPU cores. Via command-line arguments the user may specify a file to
executed in the simulated system after booting (bash scripts are recommended
but if a binary is required, please ensure it is statically linked and compiled
to X86). If nothing specified the boot will complete and the simulation will
exit.

For testing purposes, the user may pass a maximum number of ticks to run before
exiting.

Usage
-----

```sh
# Note: This script only uses X86 ISA. Ensure gem5 is compiled to X86.
# It does no harm to compile to ALL (scons build/ALL/gem5.opt) but it will
# take longer to compile.
scons build/X86/gem5.opt
./build/X86/gem5.opt ssbse-challenge-examples/x86-ubuntu-run.py \
    [--readfile=<path to script or binary>] \
    [--max-ticks=<number of ticks to run before exiting>]
```
"""

from gem5.utils.requires import requires
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.simulate.simulator import Simulator
from gem5.resources.workload import Workload
import argparse

# This runs a check to ensure the gem5 binary is compiled to include the X86
# ISA. Including this check is optional but you can encounter confusing errors
# if the gem5 binary does not have the correct ISA or coherence protocol
# compiled in.
requires(
    isa_required=ISA.X86,
)

# Here we read in the parameters passed to the configuration script.
parser = argparse.ArgumentParser(
    description="An example X86 boot script."
)

# The only positional argument accepted is the benchmark name in this script.

parser.add_argument(
    "--readfile",
    type=str,
    required=False,
    help="The path to file for the simulated system to execute after boot.",
)

parser.add_argument(
    "--max-ticks",
    type=int,
    required=False,
    help="The maximum number of ticks to run before exiting.",
)

args = parser.parse_args()

from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)

# Here we setup a Private L1, Private L2 cache heirarchy. The L1 cache is split
# in two, one for data (l1d) and one for instructions (l1u). The L2 cache is
# shared between both.
cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="16kB", l1i_size="16kB", l2_size="256kB"
)

# Setup the system memory. This is a Single Channel DDR3 1600MHz memory with
# 3GB of memory.
memory = SingleChannelDDR3_1600(size="3GB")

# Here we setup the processor. This processor has 2 X86 Timing cores.
# Timing is the CPU model which we are using. This Timing CPU model uses
# timing memory accesses to simulate the CPU interaction with cache system.
# This means that the CPU waits for the cache system to respond to a request.
# All hits, misses, and evictions are simulated. This is costly, especially
# given the CPU will always receive the same value from the memory system
# regardless.
#
# The alternative to this is the atomic CPU ("CPUTypes.ATOMIC") which estimates
# memory access time and essentially skips simulation of the cache. It is
# substantially faster than timing but not as accurate useless if simulating
# cache etups is the goal of the simulation.
# Neither of these CPUs simulate out-of-order execution. For this the O3 CPU is
# required. It will use a timing memory access. Due to the nature of
# simulating out-of-order simulation, this CPU is substantially slower than
# timing. We would not recommend it for anything other than very small code
# executions
#
# **Note**: Getting all CPU types to work with all cache hierarchy times, for
# and number of cores is a hard problem which we are still working on. If you
# encounter an error, try changing the CPU type, cache hierarchy, or number of
# of cores. "configs/example/gem5_library" contains scripts you may reference.
#
# When it doubt, use the Timing CPU. It will give you accurate timings without
# too much of a performance cost
processor = SimpleProcessor(
    core_type=CPUTypes.TIMING,
    isa=ISA.X86,
    num_cores=2,
)

# Here we setup the board. The X86Board allows for Full-System X86 simulations.
board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Here we set the Full System workload. The "workload" is the the program
# to be run in gem5. In this instance we specify a pre-build workload called
# "x86-ubuntu-18.04-boot". This will obtain a Linux kernel and a Linux 18.04
# disk iamge from our gem5-resources infrastructure and load them into the
# board. For this particular workload the disk image has been configured so
# that if a "readfile" is set, the disk image will attempt to load the file
# then execute it. If "readfile" is not set the simulation will exit after
# boot. The readfile parameter can be used to pass bash scripts or statically
# linked binaries to the simulation. 
#
# Note: If the readfile executes and does not trigger a simulation exit, the
# simulation will not exit. The
# "ssbse-challenge-examples/refs/example-script.sh" script is an example of
# executing a readfile and exiting when done.
#
# For most purpose, booking Ubuntu completely is a decent benchmark for gem5.
# Though, it should be noted that booting the OS does not invoke any floating
# point operations.
workload = Workload("x86-ubuntu-18.04-boot")
workload.set_parameter("readfile", readfile)
board.set_workload(workload)

# Here we setup the simulator. The board just specifies the the system.
# The simulator is the harness which manager the simulation as defined by the
# board.
simulator = Simulator(
    board=board,
)

# Here we enter the simulation loop. If the "max-ticks" argument is not set
# the simulation will run until completion . If the "max-ticks" argument is
# set, the simulation will exit at that tick. Though configurable, by
# default there are 1000000000000 ticks in a simulated second of gem5, or each
# tick is 1 picosecond.
#
# This is useful for running a quick sanity check on a simulation. Most gem5
# code is touched very early into the simulation. If a simulation remains
# functional for a few million ticks, it is likely that the simulation will
# complete successfully.
if args.max_ticks:
    simulator.run(max_ticks=args.max_ticks)
else:
    simulator.run()
    # The following code is commented out because it's only applicable when
    # executing the following command:
    # `./build/X86/gem5.opt ssbse-challenge-examples/x86-ubuntu-run.py \
    #        --readfile="ssbse-challenge-examples/refs/example-script.sh"`
    #
    # If you consult the "example-script.sh" file, you'll see that it contains
    # `m5 exit` commands which exit the simulation. After the first exit the
    # simulation may be entered again, entering at exactly the same point at
    # which it exited. The simulation will then continue until the second
    # `m5 exit` command is reached.
    #
    # Comment out the 3 lines of code below and see for yourself.
    #
    #print("The simulation exited. Going to start the simulation again.")
    #simulator.run()
    #print("The simulation exited again.")
