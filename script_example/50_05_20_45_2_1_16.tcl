set protocol "DEP_EXP"
create_protocol $protocol 1.0

set settle_path "./pattern/SpeedCalPat/all_1"
set move_path "./pattern/SpeedCalPat/move"
set settle_again_path $settle_path
set collect_path "./pattern/SpeedCalPat/collect"

set settle_delay 5.0
set move_delay 0.5
set settle_again_delay 2.0
set collect_delay 4.5

set loop_count 1
set loop_interval 0
set global_frequency [expr {3 * 10**6}]
set phase 180
set voltage 1.8

set init_freq_pow 6.75
set repeats_per_freq 2
set freq_range 16
set experiment_repeats 1
set length [expr {$freq_range * $repeats_per_freq}]

for {set j 0} {$j < $experiment_repeats} {incr j} {
    for {set i 0} {$i < $length} {incr i} {
        set index [expr {$i + $j * $length}]
        set move_freq [expr {10 ** ($init_freq_pow - (int($i / $repeats_per_freq)) * 0.25)}]
        add_DEP_action [format "Settle_%d" $index] $settle_path $settle_delay "Correct" $loop_count $loop_interval $move_freq $phase $voltage
        add_DEP_action [format "MOVE_%d" $index] $move_path $move_delay "Normal" $loop_count $loop_interval $move_freq $phase $voltage
        add_DEP_action [format "Settle_again_%d" $index] $settle_again_path $settle_again_delay "Correct" $loop_count $loop_interval $move_freq $phase $voltage
        add_DEP_action [format "Collect_%d" $index] $collect_path $collect_delay "Correct" $loop_count $loop_interval $global_frequency $phase $voltage
    }
}

update_gui
