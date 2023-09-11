# XRFeitoria Blender Addon

By running `xf.init_blender`, a XRFeitoria addon will be installed in your Blender.
The source code of the addon is in `src/XRFeitoriaBpy`.
It enables you to start RPC server and manage your sequences.

The addon panel is in the top-right corner of the 3D Viewport.
![](http://file.bj.zoe.sensetime.com/resources/meihaiyi/xrfeitoria/pics/blender-addon/1-addon_position.png)

Click the button `Start RPC Server` to start the RPC server. The server will listen on port 9997 to receive commands from XRFeitoria and execute them in Blender.
![](http://file.bj.zoe.sensetime.com/resources/meihaiyi/xrfeitoria/pics/blender-addon/2-start_rpc_server.png)

Click the drop down box `Active` in the `Manage sequences` section to open a sequence belonging to the current level. The objects in the sequence will be loaded to the window, and the properties of the sequence such as `fps`, `frame_start`, `frame_end` and `frame_current` will be set.
![](http://file.bj.zoe.sensetime.com/resources/meihaiyi/xrfeitoria/pics/blender-addon/3-open_sequence.png)

Click the 'x' button beside the drop down box to close the sequence.
![](http://file.bj.zoe.sensetime.com/resources/meihaiyi/xrfeitoria/pics/blender-addon/4-close_sequence.png)
