import pytest
from typing import Annotated, Optional
from typing_extensions import deprecated
from pydantic import BaseModel, PydanticUserError

# Tests behavior
def test_deprecated_field_forward_annotation() -> None:
    class Model(BaseModel):
        a: "Annotated[Test, deprecated('test')]" = 2
    
    Test = int

    Model.model_rebuild()
    assert isinstance(Model.model_fields['a'].deprecated, deprecated)
    assert Model.model_fields['a'].deprecated.message == 'test'
    
    m = Model()
    with pytest.warns(DeprecationWarning, match='test'):
        m.a
    

# Tests Root Cause (Rewritten to remove the create_module fixture)
def test_forward_ref_auto_update_no_model():
    class Foo(BaseModel):
        a: Optional['Bar'] = None

    with pytest.raises(PydanticUserError, match='`Foo` is not fully defined; you should define `Bar`,'):
        Foo(a={'b': {'a': {}}})

    class Bar(BaseModel):
        b: 'Foo'

    assert Bar.__pydantic_complete__ is True
    assert Bar.model_fields['b']._complete

    # Bar should be complete and ready to use
    b = Bar(b={'a': {'b': {}}})
    assert b.model_dump() == {'b': {'a': {'b': {'a': None}}}}

    # model_fields is *not* complete on Foo
    assert not Foo.model_fields['a']._complete
    assert Foo.__pydantic_complete__ is False

    # Foo gets auto-rebuilt during the first attempt at validation
    f = Foo(a={'b': {'a': {'b': {'a': None}}}})
    assert Foo.__pydantic_complete__ is True
    assert f.model_dump() == {'a': {'b': {'a': {'b': {'a': None}}}}}