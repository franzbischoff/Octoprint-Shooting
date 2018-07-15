; Assuming Prusa Mk2s volume: X 0-250; Y -3-210; Z 0-200

; go home
G28

; use absolute positioning for the XYZ axes
G90
; Set base speed 100 mm/s
G1 F6000
; Center on X
G1 X125

; Traverse Y
G1 Y0
G1 Y105

M400
@mpu6080 start

G1 Y210

G1 Y105
M400
@mpu6080 stop

; Sleep. Stops printer from going back to home.
;M1
