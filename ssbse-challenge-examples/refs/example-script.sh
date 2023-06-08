#!/bin/bash

echo "Hello! I am your example script running!"

# Note here, we are using the `m5` utility. If this utility is contained within
# a simulation, you may use it to commincate to the simulator. The most common
# use for this is to exit the simulation with `m5 exit`.

echo "Exiting simulation!"
sleep 3 # I like to sleep after a short script to ensure the stdout is flushed.
m5 exit

echo "Oh... we're back? I guess we didn't exit the simulation after all."
echo "Let's exit again!"
sleep 3
m5 exit