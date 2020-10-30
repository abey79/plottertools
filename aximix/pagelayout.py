import copy
import io
import itertools
import math
import os
from typing import Dict, Optional, Tuple, Union

import vpype as vp
from matplotlib.colors import hsv_to_rgb

COLORS = [
    hsv_to_rgb((h, s, v))
    for v, s, h in list(
        itertools.product(
            (0.8, 0.5),
            (1, 0.5, 0.25),
            (0, 0.14, 0.35, 0.5, 0.6, 0.75, 0.9),
        )
    )
]


class PageLayout:
    def __init__(self, path=""):
        self._path = ""
        self._landscape = False
        self._rotate = False
        self._center = True
        self._fit_to_page = False
        self._margin = 0.0
        self._page_format = vp.convert_page_format("a4")
        self._vector_data: Optional[vp.VectorData] = None
        self._layer_enabled: Dict[int, bool] = {}

        self.path = path

    @property
    def page_format(self) -> Tuple[float, float]:
        return self._page_format

    @page_format.setter
    def page_format(self, page_format: Union[str, Tuple[float, float]]):
        self._page_format = vp.convert_page_format(page_format)

    @property
    def landscape(self) -> bool:
        return self._landscape

    @landscape.setter
    def landscape(self, val: bool) -> None:
        self._landscape = val

    @property
    def rotate(self) -> bool:
        return self._rotate

    @rotate.setter
    def rotate(self, val: bool) -> None:
        self._rotate = val

    @property
    def center(self) -> bool:
        return self._center

    @center.setter
    def center(self, val: bool) -> None:
        self._center = val

    @property
    def fit_to_page(self) -> bool:
        return self._fit_to_page

    @fit_to_page.setter
    def fit_to_page(self, val: bool) -> None:
        self._fit_to_page = val

    @property
    def margin(self) -> float:
        return self._margin

    @margin.setter
    def margin(self, margin: Union[float, str]) -> None:
        self._margin = vp.convert_length(margin)

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str) -> None:
        self._path = path
        if path:
            self._vector_data = vp.read_multilayer_svg(
                path, vp.convert_length("0.05mm"), False
            )
            self._layer_enabled = {
                layer_id: True for layer_id in self._vector_data.layers
            }
        else:
            self._vector_data = None
            self._layer_enabled = {}

    @property
    def layer_count(self) -> int:
        return len(self._layer_enabled)

    def layer_enabled(self, layer_id: int) -> bool:
        return self._layer_enabled.get(layer_id, False)

    def toggle_layer_enabled(self, idx: int):
        if 0 <= idx < len(self._layer_enabled):
            self._layer_enabled[idx] = not self._layer_enabled[idx]

    def get_plot_vector_data(self) -> Optional[vp.VectorData]:
        if self._vector_data is None:
            return None

        vd = vp.VectorData()
        for layer_id, enabled in self._layer_enabled.items():
            if enabled:
                vd.layers[layer_id] = copy.deepcopy(self._vector_data.layers[layer_id])

        width, height = self.page_format
        if self.landscape:
            width, height = height, width

        if self.rotate:
            vd.rotate(-math.pi / 2)
            vd.translate(0, height)

        bounds = vd.bounds()
        if bounds is not None:
            min_x, min_y, max_x, max_y = bounds

            if self.fit_to_page:
                factor_x = (width - 2 * self.margin) / (max_x - min_x)
                factor_y = (height - 2 * self.margin) / (max_y - min_y)
                scale = min(factor_x, factor_y)

                vd.translate(-min_x, -min_y)
                vd.scale(scale)
                if factor_x < factor_y:
                    vd.translate(
                        self.margin,
                        self.margin
                        + (height - 2 * self.margin - (max_y - min_y) * scale) / 2,
                    )
                else:
                    vd.translate(
                        self.margin
                        + (width - 2 * self.margin - (max_x - min_x) * scale) / 2,
                        self.margin,
                    )
            elif self.center:
                vd.translate(
                    (width - (max_x - min_x)) / 2 - min_x,
                    (height - (max_y - min_y)) / 2 - min_y,
                )

        return vd

    def get_plot_svg(self) -> str:
        vd = self.get_plot_vector_data()

        str_io = io.StringIO()
        vp.write_svg(
            str_io,
            vd,
            page_format=tuple(reversed(self.page_format))
            if self.landscape
            else self.page_format,
            center=False,
        )

        return str_io.getvalue()

    def preview(self):
        vd = self.get_plot_vector_data()
        if vd is None:
            return

        svg_width, svg_height = self.page_format
        if self.landscape:
            svg_width, svg_height = svg_height, svg_width

        # TODO: ugly af
        with open("/tmp/.aximix_preview.svg", "w") as fp:
            vp.write_svg(
                fp,
                vd,
                page_format=(svg_width, svg_height),
                center=self.center,
                show_pen_up=True,
                color_mode="layer",
            )
            os.system(
                f"vpype read /tmp/.aximix_preview.svg rect -l 10 0 0 {svg_width} {svg_height} "
                "show -ap -u cm 2> /dev/null &"
            )

    # def preview_broken(self):
    #     vd = self.get_plot_vector_data()
    #     if vd is None:
    #         return
    #
    #     scale = vp.convert_length("1cm")
    #
    #     fig = plt.figure()
    #     ax = plt.subplot(1, 1, 1)
    #
    #     # draw page
    #     w = self.page_format[0] * scale
    #     h = self.page_format[1] * scale
    #     if self.landscape:
    #         w, h = h, w
    #     dw = 10 * scale
    #     ax.plot(
    #         np.array([0, 1, 1, 0, 0]) * w,
    #         np.array([0, 0, 1, 1, 0]) * h,
    #         "-k",
    #         lw=0.25,
    #     )
    #     ax.fill(
    #         np.array([w, w + dw, w + dw, dw, dw, w]),
    #         np.array([dw, dw, h + dw, h + dw, h, h]),
    #         "k",
    #         alpha=0.3,
    #     )
    #
    #     for layer_id, lc in vd.layers.items():
    #         color = COLORS[(layer_id - 1) % len(COLORS)]
    #
    #         layer_lines = matplotlib.collections.LineCollection(
    #             (vp.as_vector(line) * scale for line in lc),
    #             color=color,
    #             lw=1,
    #             alpha=0.5,
    #             label=str(layer_id),
    #         )
    #
    #         ax.add_collection(layer_lines)
    #
    #         if True:
    #             pen_up_lines = matplotlib.collections.LineCollection(
    #                 (
    #                     (
    #                         vp.as_vector(lc[i])[-1] * scale,
    #                         vp.as_vector(lc[i + 1])[0] * scale,
    #                     )
    #                     for i in range(len(lc) - 1)
    #                 ),
    #                 color=(0, 0, 0),
    #                 lw=0.5,
    #                 alpha=0.5,
    #             )
    #             ax.add_collection(pen_up_lines)
    #
    #     ax.invert_yaxis()
    #     ax.axis("equal")
    #
    #     ax.axis("on")
    #     ax.set_xlabel(f"[cm]")
    #     ax.set_ylabel(f"[cm]")
    #     ax.grid("on", alpha=0.2)
    #
    #     plt.ion()
    #     plt.show()
