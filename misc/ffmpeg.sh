root_path="/mnt/e/Datasets/tmp/LS_1024_155937"
cd $root_path
ffmpeg -r 30 -i "rgb/%04d.jpeg" -vcodec libx264 vis_rgb.mp4
ffmpeg -r 30 -i "vis_flow/%04d.png" -vcodec libx264 vis_flow.mp4
ffmpeg -r 30 -i "vis_depth/%04d.png" -vcodec libx264 vis_depth.mp4
ffmpeg -r 30 -i "vis_mask/%04d.png" -vcodec libx264 vis_mask.mp4
ffmpeg -i vis_rgb.mp4 -i vis_flow.mp4 -i vis_mask.mp4 -i vis_depth.mp4 -filter_complex "[0:v]pad=iw*2:ih*2[0];[0][1:v]overlay=0:1080[1];[1][2:v]overlay=1920:0[2];[2][3:v]overlay=1920:1080" output.mp4