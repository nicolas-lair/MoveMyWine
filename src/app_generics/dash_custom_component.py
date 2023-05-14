from abc import ABC, abstractmethod

from dash import Output, Input

from src.app_constant import Id


class DashCustomComponents(ABC):
    transporter_name: str

    def build_params_selector_object(self, app, location, hidden):
        div_object = self._build_params_div_object(location, hidden)
        callback = self._build_params_selector_callback(app, location)
        return div_object, callback

    @abstractmethod
    def _build_params_div_object(self, location: str = "", hidden: bool = True):
        pass

    def _build_params_selector_callback(self, app, location: str = ""):
        @app.callback(
            Output("-".join([location, self.transporter_name, Id.params_selector]), 'hidden'),
            Input(Id.transporter_dropdown, 'value')
        )
        def update_params_selector(transporter):
            return False if transporter == self.transporter_name else True

        return update_params_selector
