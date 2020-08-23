#!/usr/bin/env python3
import tempfile
import unittest
from thepipe import Provenance, disable_provenance


class TestProvenance(unittest.TestCase):
    def setUp(self):
        p = Provenance()
        p.reset()

    def test_activity(self):
        p = Provenance()
        activity_uuid = p.start_activity("test")
        assert p.current_activity.name == "test"
        p.finish_activity(activity_uuid)
        assert "test" in [b.name for b in p.backlog]
        assert len(p._activities) == 0
        assert p.backlog[0].provenance["duration"] > 0

    def test_finish_activity_with_wrong_uuid_raises(self):
        p = Provenance()
        p.start_activity("test")
        with self.assertRaises(ValueError):
            p.finish_activity("narf")

    def test_record_input_output(self):
        p = Provenance()
        p.start_activity("test")
        p.record_input("in.file")
        p.record_output("out.file")
        assert "in.file" == p.current_activity.provenance["input"][0]["url"]
        assert "out.file" == p.current_activity.provenance["output"][0]["url"]

    def test_record_configuration(self):
        p = Provenance()
        p.start_activity("test")
        p.record_configuration({"a": 1})
        assert p.current_activity.provenance["configuration"]["a"] == 1

    def test_record_configuration_updates_instead_of_overwrites(self):
        p = Provenance()
        p.record_configuration({"a": 1})
        assert p.current_activity.provenance["configuration"]["a"] == 1
        p.record_configuration({"a": 2})
        assert p.current_activity.provenance["configuration"]["a"] == 2

    def test_record_configuration_updates_and_keeps_old_config_intact(self):
        p = Provenance()
        p.record_configuration({"a": 1})
        assert p.current_activity.provenance["configuration"]["a"] == 1
        p.record_configuration({"b": 2})
        assert p.current_activity.provenance["configuration"]["b"] == 2
        assert p.current_activity.provenance["configuration"]["a"] == 1

    def test_as_json(self):
        p = Provenance()
        p.start_activity("test")
        p.as_json()

    def test_as_json_with_non_serialisable_objects_doesnt_fail(self):
        p = Provenance()
        class Foo: pass
        uuid = p.start_activity("test")
        p.record_configuration({"a": Foo()})
        p.finish_activity(uuid)
        p.as_json()

    def test_context_manager(self):
        p = Provenance()
        with p.activity("test"):
            p.record_input("whatever.file")
        assert "test" in [b.name for b in p.backlog]


    def test_outfile(self):
        p = Provenance()
        p.reset()
        fobj = tempfile.NamedTemporaryFile(delete=True)
        p._export(fobj.name)
        assert open(fobj.name, "r").read() == p.as_json(indent=2)

    def test_outfile_is_not_written_when_disabled(self):
        p = Provenance()
        p.reset()
        assert p.outfile is not None
        disable_provenance()
        assert p.outfile is None
