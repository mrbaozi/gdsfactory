from functools import partial
from typing import Dict, Optional, Union

from gdsfactory.cell import cell
from gdsfactory.component import Component
from gdsfactory.components.bend_euler import bend_euler
from gdsfactory.components.mmi1x2 import mmi1x2
from gdsfactory.components.straight import straight as straight_function
from gdsfactory.port import auto_rename_ports
from gdsfactory.types import ComponentFactory, ComponentOrFactory, Layer


@cell
def mzi(
    delta_length: float = 10.0,
    length_y: float = 0.1,
    length_x: float = 0.1,
    bend: ComponentOrFactory = bend_euler,
    straight: ComponentFactory = straight_function,
    straight_vertical: Optional[ComponentFactory] = None,
    straight_delta_length: Optional[ComponentFactory] = None,
    straight_horizontal_top: Optional[ComponentFactory] = None,
    straight_horizontal_bot: Optional[ComponentFactory] = None,
    splitter: ComponentOrFactory = mmi1x2,
    combiner: Optional[ComponentFactory] = None,
    with_splitter: bool = True,
    splitter_settings: Optional[Dict[str, Union[int, float]]] = None,
    combiner_settings: Optional[Dict[str, Union[int, float]]] = None,
    layer: Layer = (1, 0),
    **kwargs,
) -> Component:
    """Mzi.

    Args:
        delta_length: bottom arm vertical extra length
        length_y: vertical length for both and top arms
        length_x: horizontal length
        bend: 90 degrees bend library
        straight: straight function
        straight_horizontal_top: straight for length_x
        straight_horizontal_bot: straight for length_x
        straight_vertical: straight for length_y and delta_length
        splitter: splitter function
        combiner: combiner function
        with_splitter: if False removes splitter
        kwargs: cross_section settings

    .. code::

                   __Lx__
                  |      |
                  Ly     Lyr (not a parameter)
                  |      |
        splitter==|      |==combiner
                  |      |
                  Ly     Lyr (not a parameter)
                  |      |
                  | delta_length/2
                  |      |
                  |__Lx__|


    """
    combiner = combiner or splitter
    bend = partial(bend, decorator=auto_rename_ports)
    straight = partial(straight, decorator=auto_rename_ports)
    splitter = partial(splitter, decorator=auto_rename_ports)
    combiner = partial(combiner, decorator=auto_rename_ports)

    splitter_settings = splitter_settings or {}
    combiner_settings = combiner_settings or {}

    c = Component()
    cp1 = splitter(**splitter_settings, **kwargs) if callable(splitter) else splitter
    cp2 = combiner(**combiner_settings, **kwargs) if combiner else cp1

    straight_vertical = straight_vertical or straight
    straight_horizontal_top = straight_horizontal_top or straight
    straight_horizontal_bot = straight_horizontal_bot or straight
    straight_delta_length = straight_delta_length or straight
    b90 = bend(**kwargs) if callable(bend) else bend
    l0 = straight_vertical(length=length_y, **kwargs)

    y1l = cp1.ports[2].y
    y1r = cp2.ports[2].y

    e1_port_name = len(cp1.ports) - 1
    e0_port_name = len(cp1.ports)
    y2l = cp1.ports[e1_port_name].y
    y2r = cp2.ports[e1_port_name].y

    dl = abs(y2l - y1l)  # splitter ports distance
    dr = abs(y2r - y1r)  # cp2 ports distance
    delta_length_combiner = dl - dr
    assert delta_length_combiner + length_y > 0, (
        f"cp1 and cp2 port height offset delta_length ({delta_length_combiner}) +"
        f" length_y ({length_y}) >0"
    )

    l0r = straight_vertical(length=length_y + delta_length_combiner / 2, **kwargs)
    l1 = straight_delta_length(length=delta_length / 2, **kwargs)
    lxt = straight_horizontal_top(length=length_x, **kwargs)
    lxb = straight_horizontal_bot(length=length_x, **kwargs)

    cin = cp1.ref()
    cout = c << cp2

    # top arm
    blt = c << b90
    bltl = c << b90
    bltr = c << b90
    blmr = c << b90  # bend left medium right
    l0tl = c << l0
    lxtop = c << lxt
    l0tr = c << l0r

    blt.connect(port=1, destination=cin.ports[e1_port_name])
    l0tl.connect(port=1, destination=blt.ports[2])
    bltl.connect(port=2, destination=l0tl.ports[2])
    lxtop.connect(port=1, destination=bltl.ports[1])
    bltr.connect(port=2, destination=lxtop.ports[len(lxtop.ports)])
    l0tr.connect(port=1, destination=bltr.ports[1])
    blmr.connect(port=1, destination=l0tr.ports[2])
    cout.connect(port=e0_port_name, destination=blmr.ports[2])

    # bot arm
    blb = c << b90
    l0bl = c << l0
    l1l = c << l1
    blbl = c << b90
    lxbot = c << lxb
    brbr = c << b90
    l1r = c << l1
    l0br = c << l0r
    blbmrb = c << b90  # bend left medium right bottom

    blb.connect(port=2, destination=cin.ports[e0_port_name])
    l0bl.connect(port=1, destination=blb.ports[1])
    l1l.connect(port=1, destination=l0bl.ports[2])
    blbl.connect(port=1, destination=l1l.ports[2])
    lxbot.connect(port=1, destination=blbl.ports[2])
    brbr.connect(port=1, destination=lxbot.ports[len(lxbot.ports)])

    l1r.connect(port=1, destination=brbr.ports[2])
    l0br.connect(port=1, destination=l1r.ports[2])
    blbmrb.connect(port=2, destination=l0br.ports[2])
    blbmrb.connect(port=1, destination=cout.ports[e1_port_name])  # just for netlist
    # l0br.connect(2, blbmrb.ports[2])

    # west ports
    if with_splitter:
        c.add(cin)
        for port_name, port in cin.ports.items():
            if port.angle == 180:
                c.add_port(name=port_name, port=port)
    else:
        c.add_port(name=2, port=blt.ports[1])
        c.add_port(name=1, port=blb.ports[2])

    # east ports
    for i, port in enumerate(cout.ports.values()):
        if port.angle == 0:
            c.add_port(name=f"E{i}", port=port)

    # Add any non-optical ports from bottom and bottom arms

    c.add_ports(lxtop.get_ports_list(layers_excluded=(layer,)), prefix="DC_top")
    c.add_ports(lxbot.get_ports_list(layers_excluded=(layer,)), prefix="DC_bot")

    auto_rename_ports(c)

    # aliases
    # top arm
    c.aliases["blt"] = blt
    c.aliases["bltl"] = bltl
    c.aliases["bltr"] = bltr
    c.aliases["blmr"] = blmr
    c.aliases["l0tl"] = l0tl
    c.aliases["lxtop"] = lxtop
    c.aliases["l0tr"] = l0tr

    # bot arm
    c.aliases["blb"] = blb
    c.aliases["l0bl"] = l0bl
    c.aliases["l1l"] = l1l
    c.aliases["blbl"] = blbl
    c.aliases["lxbot"] = lxbot
    c.aliases["brbr"] = brbr
    c.aliases["l1r"] = l1r
    c.aliases["l0br"] = l0br
    c.aliases["blbmrb"] = blbmrb

    c.auto_rename_ports()
    return c


if __name__ == "__main__":
    import gdsfactory as gf

    # delta_length = 116.8 / 2
    # print(delta_length)
    # c = mzi(delta_length=delta_length, with_splitter=False)
    # c.pprint_netlist()

    c = mzi(
        delta_length=20,
        straight_horizontal_top=gf.c.straight_heater_metal,
        straight_horizontal_bot=gf.c.straight_heater_metal,
        length_x=50,
    )
    c = mzi(delta_length=10)
    c.show(show_subports=False)
    # c.show()
    c.pprint()
    # n = c.get_netlist()
    # c.plot()
    # print(c.get_settings())
