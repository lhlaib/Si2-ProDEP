set protocol "DEP_EXP"
create_protocol $protocol 1.0

set settle_path "./pattern/SpeedCalPat/all_1"
set move_path "./pattern/SpeedCalPat/move"
set settle_again_path $settle_path
set collect_path "./pattern/SpeedCalPat/collect"

set settle_delay 5.0
set move_delay 2.0
set settle_again_delay 2.0
set collect_delay 4.5

set loop_count 1
set loop_interval 0
set global_frequency [expr {3 * 10**6}]
set phase 180
set voltage 1.8

set init_freq_pow 6.75
set repeats 5
for {set i 0} {$i < 50} {incr i} {
    set move_freq [expr {10 ** ($init_freq_pow - (int($i / $repeats)) * 0.25)}]
    add_DEP_action "Settle_$i" $settle_path $settle_delay "Correct" $loop_count $loop_interval $global_frequency $phase $voltage
    add_DEP_action "MOVE_$i" $move_path $move_delay "Normal" $loop_count $loop_interval $move_freq $phase $voltage
    add_DEP_action "Settle_again_$i" $settle_again_path $settle_again_delay "Correct" $loop_count $loop_interval $global_frequency $phase $voltage
    add_DEP_action "Collect_$i" $collect_path $collect_delay "Correct" $loop_count $loop_interval $global_frequency $phase $voltage
}

update_gui
run_protocol