"""
Copyright (c) 2018-2020 Intel Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import numpy as np

from ..adapters import Adapter
from ..representation import ReIdentificationPrediction


class ReidAdapter(Adapter):
    """
    Class for converting output of Reid model to ReIdentificationPrediction representation
    """
    __provider__ = 'reid'
    prediction_types = (ReIdentificationPrediction, )

    def configure(self):
        """
        Specifies parameters of config entry
        """
        self.grn_workaround = self.launcher_config.get("grn_workaround", True)

    def process(self, raw, identifiers, frame_meta):
        """
        Args:
            identifiers: list of input data identifiers
            raw: output of model
        Returns:
            list of ReIdentificationPrediction objects
        """
        raw_prediction = self._extract_predictions(raw, frame_meta)
        self.select_output_blob(raw_prediction)
        prediction = raw_prediction[self.output_blob]

        if self.grn_workaround:
            # workaround: GRN layer
            prediction = self._grn_layer(prediction)

        return [ReIdentificationPrediction(identifier, embedding.reshape(-1))
                for identifier, embedding in zip(identifiers, prediction)]

    @staticmethod
    def _grn_layer(prediction):
        GRN_BIAS = 0.000001
        sum_ = np.sum(prediction ** 2, axis=1)
        prediction = prediction / np.sqrt(sum_[:, np.newaxis] + GRN_BIAS)

        return prediction

    def _extract_predictions(self, outputs_list, meta):
        if not (meta[-1] or {}).get('multi_infer', False):
            return outputs_list[0] if not isinstance(outputs_list, dict) else outputs_list

        if len(outputs_list) == 2:
            self.select_output_blob(outputs_list[0])
            emb1, emb2 = outputs_list[0][self.output_blob], outputs_list[1][self.output_blob]
            return {self.output_blob: emb1 + emb2}

        return outputs_list[0]
