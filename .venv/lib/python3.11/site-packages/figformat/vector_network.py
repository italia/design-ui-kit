import struct


def decode(fig, blob_id, scale, style_override_table):
    network = bytes(fig["blobs"][blob_id]["bytes"])

    i = 0
    num_vertices = struct.unpack("<I", network[i : i + 4])[0]
    i += 4
    num_segments = struct.unpack("<I", network[i : i + 4])[0]
    i += 4
    num_regions = struct.unpack("<I", network[i : i + 4])[0]
    i += 4

    vertices = []
    for vertex in range(num_vertices):
        # Should include stroke cap/limit, corner radius, mirroring, etc.
        style_id = struct.unpack("<I", network[i : i + 4])[0]

        # Coordinates
        x, y = struct.unpack("<ff", network[i + 4 : i + 12])

        vertices.append(decode_vertex(x, y, scale, style_override_table, style_id))
        i += 12

    segments = []
    for segment in range(num_segments):
        # No idea what it's for
        style_id = struct.unpack("<I", network[i : i + 4])[0]

        # Start vertex + tangent vector
        v1 = struct.unpack("<I", network[i + 4 : i + 8])[0]
        t1x, t1y = struct.unpack("<ff", network[i + 8 : i + 16])

        # End vertex + tangent vector
        v2 = struct.unpack("<I", network[i + 16 : i + 20])[0]
        t2x, t2y = struct.unpack("<ff", network[i + 20 : i + 28])

        segments.append(decode_segment(v1, v2, t1x, t1y, t2x, t2y, scale))
        i += 28

    regions = []
    for region in range(num_regions):
        # Flags should include winding rule
        flags, num_loops = struct.unpack("<II", network[i : i + 8])
        winding_rule = "NONZERO" if flags % 2 else "ODD"
        style_id = flags >> 1
        i += 8

        loops = []
        for loop in range(num_loops):
            num_loop_vertices = struct.unpack("<I", network[i : i + 4])[0]
            i += 4

            loop_vertices = []
            for vertex in range(num_loop_vertices):
                loop_vertices.append(struct.unpack("<I", network[i : i + 4])[0])
                i += 4
            loops.append(loop_vertices)

        regions.append(
            {
                "loops": loops,
                "style": style_override_table.get(style_id, {"styleID": style_id}),
                "windingRule": winding_rule,
            }
        )

    return {"regions": regions, "segments": segments, "vertices": vertices}


def decode_vertex(x, y, scale, style_override_table=None, style_id=None):
    vertex = {
        "x": 0 if (x == 0 or scale["x"] == 0) else x / scale["x"],
        "y": 0 if (y == 0 or scale["y"] == 0) else y / scale["y"],
    }

    if style_id:
        vertex["style"] = style_override_table.get(style_id, {"styleID": style_id})

    return vertex


def decode_segment(v1, v2, t1x, t1y, t2x, t2y, scale):
    return {
        "start": v1,
        "end": v2,
        "tangentStart": decode_vertex(t1x, t1y, scale),
        "tangentEnd": decode_vertex(t2x, t2y, scale),
    }
