import constants
import utils
import utils_actor
import utils_sequencer
from custom_movie_pipeline import CustomMoviePipeline
from Sequence import Sequence


class XRFeitoriaUnrealFactory:
    utils = utils
    utils_sequencer = utils_sequencer
    utils_actor = utils_actor
    constants = constants
    SubSystem = constants.SubSystem
    CustomMoviePipeline = CustomMoviePipeline
    Sequence = Sequence
