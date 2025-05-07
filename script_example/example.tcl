set protocol "DEP"
create_protocol $protocol 1.0

set action_name "DEP_action00"
set folder_path "./pattern/divide/divide2"
set pattern_interval 0.3
set timer_mode "Correct"
set loop_interval 0
set loop_count 1
set frequency [expr {10**6}]
set phase 180
set voltage 1.8

add_DEP_action $action_name $folder_path $pattern_interval $timer_mode $loop_count $loop_interval $frequency $phase $voltage
update_gui

add_DEP_action $action_name $folder_path $pattern_interval $timer_mode $loop_count $loop_interval $frequency $phase $voltage
update_gui