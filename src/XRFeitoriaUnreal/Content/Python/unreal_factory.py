import constants
import utils
import utils_actor
from custom_movie_pipeline import CustomMoviePipeline
from sequence import Sequence


class XRFeitoriaUnrealFactory:
    utils = utils
    utils_actor = utils_actor
    constants = constants
    SubSystem = constants.SubSystem
    CustomMoviePipeline = CustomMoviePipeline
    Sequence = Sequence
