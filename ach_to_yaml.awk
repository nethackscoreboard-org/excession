# Awk script that transforms the achievement names and descriptions given as
# tab-separated lines of input into ready-for-loaddata format.
# This shouldn't be run on its own, it's part of ach_to_yaml.sh.

# Sample line of input is something like:
# Ach Name\tLong Ach Description
# where the trailing , is expected on all lines except the last

{
    # bit offset within tnntachieveX (1 << offset corresponds to this
    # achievement)
    off = ((NR - 1) % 64); # compensate for NR starting at 1 rather than 0
    # the 'X' number in 'tnntachieveX' field
    X = ((NR - 1) - off) / 64;
    #replace("\\\"", "\"", $0) # convert C-style \" to just quotation marks
    print  "- model: scoreboard.achievement"
    print  "  fields:"
    printf "    name: \"%s\"\n", $1
    printf "    description: \"%s\"\n", $2
    printf "    xlogfield: \"tnntachieve%d\"\n", X
    printf "    bit: %d\n", off
}
