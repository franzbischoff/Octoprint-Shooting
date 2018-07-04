; Assuming Prusa Mk2s volume: X 0-250; Y -3-210; Z 0-200

; go home
G28
; Set base speed 100 mm/s
G1 F6000
; Center on X
G1 X125

; Traverse Y 3 times
G1 Y10
G1 Y190
G1 Y10
G1 Y190
G1 Y10
G1 Y190
G1 Y100

; Sleep. Stops printer from going back to home.
M1
