# gem5 for SSBSE Challenge Track 2023

This repository has been designed for use in the SSBSE Challenge Track 2023.
It is a copy of https://github.com/gem5/gem5, made on June 7th, with the following amendments:

* The v23.0 staging branch has been merged into stable to give challenge track attendees easy access to the latest gem5 features and improvements.
* The "ssbse-challenge-examples" directory has been added to provide some scripts which show example systems which may be optimized.

The following subsections should aid those who wish to target gem5 for the 2023 SSBSE Challenge Track.

## Getting Started with gem5

### Requirements

gem5 should run on all major OS (Linux, Mac OS X, Windows) though we recommend Ubuntu as we develop and regularly test on those systems.

We recommend building and running gem5 on a system with at least 6GB of memory5.
The memory consumed by gem5 during a simulation depends on the system simulated.
This should be taken into account when trying to run multiple simulations in parallel.

The following dependencies must be available to compile and run gem5:

* gcc: gcc is used to compile gem5. Version >=7 must be used. We support up to gcc Version 12.
* Clang: Clang can also be used as an alternative to gcc. At present, we support Clang 6 to Clang 14 (inclusive).
* SCons : gem5 uses SCons as its build system. SCons 3.0 or greater must be used.
* Python 3.6+ : gem5 relies on Python development libraries. gem5 can only be compiled and run in environments using Python 3.6 or above.
* m4: A macro processor used in the compilation of gem5

The following is an APT install command known to provide all required dependencies:

```sh
apt -y install build-essential m4 scons python3-dev
```

### Building

In the root directory of the repository, you can compile gem5 using `scons build/{ISA}/gem5.{variant} -j {threads}`. The placeholders are:

* `{ISA}`: The Instruction Set Architecture to be compiled into the gem5 binary. `X86`, `ARM`, and `RISCV` are the best supported option. We recommend using `ALL` which includes all gem5 ISA though this does take longer to compile.
* `variant`: Specifies compiler options. Three exist: `debug` which includes runtime debugging support (required for GDB and other debugging tools); `fast` which optimizes aggressively and does not include debugging support; and `opt` which optimizes while maintaining debugging support. We recommend `opt` unless you require faster compilation (`debug`) or faster execution (`fasts).
* `{threads}`: Specifies the number of threads to compile gem5 with.
We recommend allocating as much as possible.
A single-threaded gem5 compilation may take over 30 minutes to complete.

We recommend:

```sh
scons build/ALL/gem5.opt -j `nproc`
```

#### Additional compiler options

* `--gprof`: A flag which allows gem5 to be used with the gprof profiling tool.
Example usage: `scons build/ALL/gem5.opt --gprof`.
* `--pprof`: A flag which allows gem5 to be used with the pprof profiling tool.
Example usage: `scons build/ALL/gem5.opt --pprof`.

## gem5: The basics and Hello World

gem5 works like an interpreter.
You pass a file to be interpreted by the gem5 binary as a command line argument.
gem5 then uses this file to build and run a simulation.
The file passed to gem5 is a description of the system to simulation.
These files called different names depending on the documentation but we shall refer to these as "gem5 configuration files" or "config files".

The config files are written in Python which means these files can contain logic, interact with the wider computer system, and anything else Python permits.

If you look into "ssbse-challenge-examples/hello.py" you can see an example of a gem5 configuration file.
Please read through the comments and see if you can understand what's going on.

To run it you pass it to gem5:

```sh
./build/ALL/gem5.opt ssbse-challenge-examples/hello.py
```

This will run a simple simulation which prints "hello world" to the terminal.

Any parameters passed after the config file in the command line are passed to the config file.
In the "hello.py" example we can specify the ISA to run with the `--isa` flag.
By default it will run X86 but ARM and RISCV are options.
To run an ARM simulation you can therefore run:

```sh
./build/ALL/gem5.opt ssbse-challenge-examples/hello.py --isa ARM
```

### Seeing your output

gem5 will output statistics and other information to the "m5out" directory.
The statistics files will let you know the simulated time,
cache hits and misses, and most things you'd want to know about your system.

## gem5 at a high level

Almost everything in gem5 can be broken down into "SimObjects", the "events" they schedule, and the connections between the SimObjects via "ports".

"SimObjects" are the building blocks of a gem5 simulation.
They can theoretically represent anything.
They are a black box that waits for messages via their "Receive" ports, schedules events, and communicates with other SimObjects via their "Request" ports.
An example of a SimObject is `X86O3CPU`, an X86 Out-Of-Order CPU.
Another example would be `SingleChannelDDR3_1600`, a single-channel DDR3 memory system.

gem5 is a Discreet Event Simulator.
Events are scheduled to run in a single event queue shared between all SimObjects
which may access schedule events.
At a technical level an event is pointer to a function and the parameters that should be passed to it at the scheduled tick.

As a basic toy example, imagine a "CPU" SimObject and a "memory" SimObject both connected to each other bidirectionally via their ports.
It's important to simulate the latency between the CPU and memory when running the simulation so if the CPU requests a value from a memory location, it cannot immediately return the value on the same simulation tick.

An example of to simulate latency in gem5 would be for the CPU object to communicate to the memory object, via their ports, that it requires a particular value held at a particular address.
This would trigger a function in memory object which processes requests from this port.
In order to simulate latency the memory object would schedule an event at the latency's time length in the future (i.e., if the memory latency is 10 nanoseconds the event would be scheduled 10 nanoseconds in the future).
This event would be a pointer to a function, with parameters, in the memory SimObject which when executed would retrieve the memory at the address end return it to the CPU via the ports .

The simulator would then moved through the event queue and execute the scheduled events in the order they are scheduled.
When the memory request event is reached, the function would be called and the CPU would process the returned value, likely scheduling future events for processing of that instruction.

This is a very high-level conceptualization of gem5 but may serve useful in your work.
A tutorial which shows how to work with SimObjects in a config file (as well as develop your own, if needed) can be found here: https://www.gem5.org/documentation/learning_gem5/introduction/.

## A Typical gem5 Simulation

The "ssbse-challenge-examples/x86-ubuntu-run.py" example shows a typical gem5 simulation.
Please open and read through this file.
Comments have been added explaining what the code does and how it may be used.

As the simulation is running you can find a log of the terminal output in
"m5out".
This can be useful for looking to see how your simulation is doing.

The following subsections highlight its usage.

### Boot then exit

```sh
./build/ALL/gem5.opt ssbse-challenge-examples/x86-ubuntu-run.py
```

This will run a full-system X86 boot of Ubuntu 18.04.
The simulation will exit immediately after boot.
Expect this to take anywhere from 20 minutes to an hour to complete.

### Boot then run a script

```sh
./build/ALL/gem5.opt ssbse-challenge-examples/x86-ubuntu-run.py \
    --readfile="$(pwd)/ssbse-challenge-examples/refs/example-script.sh"
```

This will, again, run a full-system X86 boot of Ubuntu 18.04
Instead of exiting immediately after boot it will execute the "ssbse-challenge-examples/refs/example-script.sh" script.

Please open and read "ssbse-challenge-examples/refs/example-script.sh", it
shows how to trigger the simulator to exit.

```sh
./build/ALL/gem5.opt ssbse-challenge-examples/x86-ubuntu-run.py \
    --max-ticks=10000000
```

This will run a full-system X86 boot of Ubuntu 18.04 for 10 million ticks (0.1 microseconds) before exiting.

## Tests

If you wish to test gem5 for bugs, you can use tests provided to you by the gem5 project.
The following subsections outline different tests you may run.

**Important testing notes:**

* gem5 passing tests does not necessarily indicate no bugs are present.
While we try to cover common use-cases, we do not have 100% code-coverage.
* Some tests will not run if your system is unable to. For example, tests
which require X86 KVM (Kernel Virtual Machine) will not run on machines that are not-X86 or do not have KVM enabled.
* Executing all the gem5 will take days.
In the following subsections we give time estimates for these as guidance.

### CPP Unittests

```sh
scons build/ALL/unittests.opt -j <threads>
```

This will run CPP unittests using GTest.
They mostly tests core gem5 simulation functionality and will take less than 5 minutes to run on a single thread.

### Python Unittests

```sh
build/ALL/gem5.opt tests/run_pyunit.py
```

This will test code written in Python using Python's "unittest" module.
The coverage of these tests is low, as they are relatively new.
Running these tests requires compilation of gem5.
Changes to the codebase will require recompilation though recompilation can be done in a few minutes if not many files were touched.
They will take longer to run the first time as resources are downloaded but they cached for future use so this is a one-time cost.
After the resources have been cached locally the tests can run in under a minute.

### Testlib tests

These are by far the most comprehensive tests in gem5, though they are also the most costly to run.
They run gem5 simulations and verify the results obtained.

They can be executed using:

```sh
cd tests
./main.py run --length {length} -j {comp-threads} -t {run-threads}
```

The placeholder `{length}` can be either `quick`, `long`, or `very-long`.
These are classifications of tests. They are as follows:

* `quick` tests are the fastest and will take around 1.5 to 5 hours to complete depending on the system and threads you can allocate.
* `long` tests will typically take over 12 hours to complete.
* `very-long` tests will typically take 3 days to complete

Please note that these sets of tests are disjoint. `quick` tests do not include `long` tests and `long` tests do not include `very-long` tests.

The these tests compile gem5 as part of their function.
To specify the number of threads to compile gem5 with use the `-j` flag.

The `-t` flag can be used to specify how many tests may be run in parallel.
Use this with caution.
A single gem5 thread may consume as much as 6GB of memory.
Running multiple tests in parallel may cause your system to run out of memory and crash.

We would recommend running the `quick` tests and foregoing the rest.
These tests cover most use-cases.

## Compiler tests

```sh
./tests/compiler-tests.sh
```

These tests ensure all the various ways gem5 can be compiled, across different
versions of clang and gcc, still work.
This script requires docker to function.

## Common questions/complaints and my response

* __"I get a lot of warnings when running gem5"__: gem5 is noisy.
Warnings in gem5 are not necessarily indicative of a problem.
They are merely our mechanism for communicating things that may be a problem, even if unlikely.
* __"gem5 is slow"__: It is, you can expect at least a 10k to 100k times slow down. So one simulated second can be 100k seconds to run on the host machine .
If you aware willing to sacrifice accuracy for speed, try using a different CPU core (ATOMIC for example). If possible you may want to use the KVM core, though this requires a compatible host machine: https://www.gem5.org/documentation/general_docs/using_kvm/. There is also a technique known as "checkpointing" to save a gem5 state and return to it later. This can be used to avoid booting the system every time you wish to run a simulation. It is documented here: https://www.gem5.org/documentation/general_docs/checkpointing/.
* __"gem5 is using a lot of memory"__: gem5 is a memory intensive application. It is not uncommon for gem5 to use 6GB of memory per thread. If you are running multiple gem5 simulations in parallel, you may run out of memory. If you are running gem5 on a machine with limited memory, you may wish to reduce the number of threads you are using.



## Additional resources and getting help

If you are struggling, please consult the following resources:

* The gem5 website: https://www.gem5.org
* The learning gem5 tutorial: https://www.gem5.org/documentation/learning_gem5/.
A good tutorial that starts from the basics of gem5.
This focuses on building and connecting SimObjects.
* The gem5 standard library tutorial: https://www.gem5.org/documentation/gem5-stdlib/overview
A tutorial demonstrating various parts of the gem5 standard library.
* The gem5 Bootcamp archive: https://www.youtube.com/playlist?list=PL_hVbFs_loVSaSDPr1RJXP5RRFWjBMqq3 and https://gem5bootcamp.github.io/gem5-bootcamp-env/.
In 2022 UC Davis ran a 5 day bootcamp on gem5.
In the YouTube channel and the website linked is an archive of the event.
This can get very detailed.

If you wish to get help from the community, you may do so via the mailing lists:
https://www.gem5.org/mailing_lists/

We also have a slack channel you may access with:
https://join.slack.com/t/gem5-workspace/shared_invite/zt-1c8go4yjo-LNb7l~BZ0FagwmVxX08y9g.

