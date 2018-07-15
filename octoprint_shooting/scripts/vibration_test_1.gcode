; Assuming Prusa Mk2s volume: X 0-250; Y -3-210; Z 0-200

G28 ; go home

G90 ; use absolute positioning for the XYZ axes
G1 F6000 ; Set base speed 100 mm/s
G1 Z10 ; Goes up a little
G1 X125 ; Center on X

; Traverse Y
G1 Y0
G1 Y105
M400 ; Wait finishing movements
@mpu6080 start ; Start recording

G1 Y210 ; back to front pass
G1 Y0   ; front to back pass
G1 Y210 ; end of pass

G1 Y105 ; return to center
M400 ; Wait finishing movements
@mpu6080 stop ; Stop recording

G1 Y0 ; keep moving to home Y

; Sleep. Stops printer from going back to home.
; M1
