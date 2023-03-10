import codecs
import ctypes
from collections import OrderedDict
import zlib
import struct
import io


class KiwiReader:
    def __init__(self, reader):
        self._reader = reader

    def byte(self):
        return self._reader.read(1)[0]

    def bool(self):
        return self.byte() > 0

    def uint(self):
        uint = 0
        shift = 0
        for shift in range(0, 36, 7):
            b = self.byte()
            uint |= (b & 127) << shift
            if b < 128:
                break

        return uint

    def float(self):
        b = self.byte()
        if b == 0:
            return 0.0

        bits = b | self.byte() << 8 | self.byte() << 16 | self.byte() << 24
        bits = (bits << 23) | (bits >> 9)

        return ctypes.c_float.from_buffer(ctypes.c_uint32(bits)).value

    def int(self):
        v = self.uint()
        return ~(v >> 1) if v & 1 else v >> 1

    def string(self):
        string = ""
        decoder = codecs.lookup("utf8").incrementaldecoder()
        while not (string and string[-1] == "\x00"):
            ch = ""
            while not ch:
                ch = decoder.decode(self._reader.read(1))
            string += ch

        return string[:-1]


class KiwiSchema:
    def __init__(self, reader):
        kw = KiwiReader(reader)

        self.types = []
        for _ in range(kw.uint()):
            name = kw.string()
            kind = kw.byte()

            fields = OrderedDict()
            for _ in range(kw.uint()):
                field = KiwiSchema._decode_field(kw)

                fields[field["value"]] = field

            self.types.append({"name": name, "kind": kind, "fields": fields})

    def _decode_field(kw):
        return {
            "name": kw.string(),
            "type": kw.int(),
            "array": kw.bool(),
            "value": kw.uint(),
        }


class KiwiDecoder:
    TYPES = ["bool", "byte", "int", "uint", "float", "string"]
    KINDS = ["ENUM", "STRUCT", "MESSAGE"]

    def __init__(self, schema, type_converters):
        self.schema = schema
        self.type_converters = type_converters

    def decode(self, reader, root):
        kw = KiwiReader(reader)
        root_type = [t for t in self.schema.types if t["name"] == root][0]
        return self._decode_message(kw, root_type)

    def _decode_message(self, kw, type):
        obj = {}
        while (fid := kw.uint()) != 0:
            field = type["fields"][fid]
            ftype = field["type"]

            obj[field["name"]] = self._decode_type(kw, ftype, field["array"])

        return obj

    def _decode_struct(self, kw, type):
        return {
            f["name"]: self._decode_type(kw, f["type"], f["array"])
            for f in type["fields"].values()
        }

    def _decode_enum(self, kw, type):
        value = kw.uint()
        return type["fields"][value]["name"]

    def _decode_type(self, kw, type_id, array):
        obj = self._decode_type_inner(kw, type_id, array)

        type_converter = self.type_converters.get(self.schema.types[type_id]["name"])
        if not array and type_converter:
            obj = type_converter(obj)

        return obj

    def _decode_type_inner(self, kw, type_id, array):
        if array:
            return [self._decode_type(kw, type_id, False) for i in range(kw.uint())]

        if type_id < 0:
            primitive = self.TYPES[~type_id]
            return kw.__getattribute__(primitive)()
        else:
            type = self.schema.types[type_id]
            match type["kind"]:
                case 0:
                    return self._decode_enum(kw, type)
                case 1:
                    return self._decode_struct(kw, type)
                case 2:
                    return self._decode_message(kw, type)
                case other:
                    raise "Unknown"


def decode(reader, type_converters):
    SUPPORTED_VERSIONS = [15, 20]

    header = reader.read(12)
    fig_version = struct.unpack("<I", header[8:12])[0]
    if fig_version not in SUPPORTED_VERSIONS:
        raise Exception(
            f"Unsupported .fig version. File = {fig_version} / Supported = {SUPPORTED_VERSIONS}"
        )

    segment_header = reader.read(4)
    size = struct.unpack("<I", segment_header)[0]
    data = io.BytesIO(zlib.decompress(reader.read(size), wbits=-15))
    schema = KiwiSchema(data)

    segment_header = reader.read(4)
    size = struct.unpack("<I", segment_header)[0]
    data = io.BytesIO(zlib.decompress(reader.read(size), wbits=-15))
    return KiwiDecoder(schema, type_converters).decode(data, "Message")
