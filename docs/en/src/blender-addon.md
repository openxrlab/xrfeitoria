# XRFeitoria Blender Addon

By running `xf.init_blender`, a XRFeitoria addon will be installed in your Blender.
The source code of the addon is in `src/XRFeitoriaBpy`.
It enables you to start RPC server and manage your sequences.

The addon panel is in the top-right corner of the 3D Viewport.
![](https://github.com/user-attachments/assets/6cbf22a4-a26e-47b3-b164-8a3f6cd76fa3)

Click the button `Start RPC Server` to start the RPC server. The server will listen on port 9997 to receive commands from XRFeitoria and execute them in Blender.
![](https://github.com/user-attachments/assets/4908eb58-7ca9-40fd-b88c-329e7727e51a)

Click the drop down box `Active` in the `Manage sequences` section to open a sequence belonging to the current level. The objects in the sequence will be loaded to the window, and the properties of the sequence such as `fps`, `frame_start`, `frame_end` and `frame_current` will be set.
![](https://github.com/user-attachments/assets/0af64a96-af06-404a-9a59-7cf13cd8e800)

Click the 'x' button beside the drop down box to close the sequence.
![](https://github.com/user-attachments/assets/6a5d9543-2e5a-406b-8f96-8de54a28b725)
