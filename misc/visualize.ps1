$Plugin_Path="D:/Feitoria/xrfeitoria-gear";
$Output_Path="D:/Feitoria/dataset/LS_Demo";
$res_x=1280;
$res_y=720;

# visualize
cd $Plugin_Path
python misc/visualize.py -i $Output_Path -o $Output_Path/vis_mask --img_pattern "mask/*" -t mask;
python misc/visualize.py -i $Output_Path -o $Output_Path/vis_depth --img_pattern "depth/*" -t depth;
python misc/visualize.py -i $Output_Path -o $Output_Path/vis_flow --img_pattern "optical_flow/*" -t flow;

# to video
cd $Output_Path;
ffmpeg -r 30 -i "rgb/%04d.jpeg" -vcodec libx264 vis_rgb.mp4;
ffmpeg -r 30 -i "vis_flow/%04d.png" -vcodec libx264 vis_flow.mp4;
ffmpeg -r 30 -i "vis_depth/%04d.png" -vcodec libx264 vis_depth.mp4;
ffmpeg -r 30 -i "vis_mask/%04d.png" -vcodec libx264 vis_mask.mp4;
ffmpeg -i vis_rgb.mp4 -i vis_flow.mp4 -i vis_mask.mp4 -i vis_depth.mp4 -filter_complex "[0:v]pad=iw*2:ih*2[0];[0][1:v]overlay=0:$res_y[1];[1][2:v]overlay=${res_x}:0[2];[2][3:v]overlay=${res_x}:${res_y}" output.mp4;

echo "visulization video: $Output_Path/output.mp4";
cd $Plugin_Path