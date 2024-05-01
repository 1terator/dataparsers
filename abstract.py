from abc import abstractmethod, ABC
from typing import List, Tuple


class AbstractParseService(ABC):
    @abstractmethod
    async def parse(self) -> List:
        pass

    @abstractmethod
    def get_parsed_data_names(self) -> Tuple:
        pass
