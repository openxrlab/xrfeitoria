from custom_movie_pipeline import CustomMoviePipeline

level = '/Game/Maps/DefaultMap'
sequence_name = '/Game/Sequences/LS_Demo'
CustomMoviePipeline.add_job_to_queue_with_render_config(
    level=level, level_sequence=sequence_name)
CustomMoviePipeline.render_queue()