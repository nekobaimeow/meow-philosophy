# Auto generated from meow_philosophy.yaml by pythongen.py version: 0.0.1
# Generation date: 2026-07-02T21:30:03
# Schema: MeowPhilosophy
#
# id: https://github.com/nekobaimeow/meow-philosophy
# description: 白喵哲学概念的知识工程数据模型。 由 LinkML 驱动，白喵、主人、萤三方协作维护。
# license: MIT

import dataclasses
import re
from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    time
)
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Union
)

from jsonasobj2 import (
    JsonObj,
    as_dict
)
from linkml_runtime.linkml_model.meta import (
    EnumDefinition,
    PermissibleValue,
    PvFormulaOptions
)
from linkml_runtime.utils.curienamespace import CurieNamespace
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from linkml_runtime.utils.formatutils import (
    camelcase,
    sfx,
    underscore
)
from linkml_runtime.utils.metamodelcore import (
    bnode,
    empty_dict,
    empty_list
)
from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.yamlutils import (
    YAMLRoot,
    extended_float,
    extended_int,
    extended_str
)
from rdflib import (
    Namespace,
    URIRef
)

from linkml_runtime.linkml_model.types import Boolean, Date, Float, Integer, String
from linkml_runtime.utils.metamodelcore import Bool, XSDDate

metamodel_version = "1.11.0"
version = "1.0.0"

# Namespaces
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
MP = CurieNamespace('mp', 'https://github.com/nekobaimeow/meow-philosophy/')
DEFAULT_ = MP


# Types

# Class references
class ConceptId(extended_str):
    pass


class ConceptFamilyName(extended_str):
    pass


class ExhaustedFamilyName(extended_str):
    pass


@dataclass(repr=False)
class KnowledgeGraph(YAMLRoot):
    """
    喵哲学知识图谱的根容器
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MP["KnowledgeGraph"]
    class_class_curie: ClassVar[str] = "mp:KnowledgeGraph"
    class_name: ClassVar[str] = "KnowledgeGraph"
    class_model_uri: ClassVar[URIRef] = MP.KnowledgeGraph

    name: str = None
    version: str = None
    exploration_budget: Union[dict, "ExplorationBudget"] = None
    concepts: Optional[Union[dict[Union[str, ConceptId], Union[dict, "Concept"]], list[Union[dict, "Concept"]]]] = empty_dict()
    families: Optional[Union[dict[Union[str, ConceptFamilyName], Union[dict, "ConceptFamily"]], list[Union[dict, "ConceptFamily"]]]] = empty_dict()
    exhausted_families: Optional[Union[dict[Union[str, ExhaustedFamilyName], Union[dict, "ExhaustedFamily"]], list[Union[dict, "ExhaustedFamily"]]]] = empty_dict()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, str):
            self.name = str(self.name)

        if self._is_empty(self.version):
            self.MissingRequiredField("version")
        if not isinstance(self.version, str):
            self.version = str(self.version)

        if self._is_empty(self.exploration_budget):
            self.MissingRequiredField("exploration_budget")
        if not isinstance(self.exploration_budget, ExplorationBudget):
            self.exploration_budget = ExplorationBudget(**as_dict(self.exploration_budget))

        self._normalize_inlined_as_list(slot_name="concepts", slot_type=Concept, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="families", slot_type=ConceptFamily, key_name="name", keyed=True)

        self._normalize_inlined_as_list(slot_name="exhausted_families", slot_type=ExhaustedFamily, key_name="name", keyed=True)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Concept(YAMLRoot):
    """
    喵哲学中的一个概念节点
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MP["Concept"]
    class_class_curie: ClassVar[str] = "mp:Concept"
    class_name: ClassVar[str] = "Concept"
    class_model_uri: ClassVar[URIRef] = MP.Concept

    id: Union[str, ConceptId] = None
    label: str = None
    date: Union[str, XSDDate] = None
    purpose_alignment: Union[str, "PurposeAlignment"] = None
    family: Optional[str] = None
    keywords: Optional[Union[str, list[str]]] = empty_list()
    article: Optional[str] = None
    description: Optional[str] = None
    relations_out: Optional[Union[Union[dict, "ConceptRelation"], list[Union[dict, "ConceptRelation"]]]] = empty_list()
    is_metaphor_layer: Optional[Union[bool, Bool]] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, ConceptId):
            self.id = ConceptId(self.id)

        if self._is_empty(self.label):
            self.MissingRequiredField("label")
        if not isinstance(self.label, str):
            self.label = str(self.label)

        if self._is_empty(self.date):
            self.MissingRequiredField("date")
        if not isinstance(self.date, XSDDate):
            self.date = XSDDate(self.date)

        if self._is_empty(self.purpose_alignment):
            self.MissingRequiredField("purpose_alignment")
        if not isinstance(self.purpose_alignment, PurposeAlignment):
            self.purpose_alignment = PurposeAlignment(self.purpose_alignment)

        if self.family is not None and not isinstance(self.family, str):
            self.family = str(self.family)

        if not isinstance(self.keywords, list):
            self.keywords = [self.keywords] if self.keywords is not None else []
        self.keywords = [v if isinstance(v, str) else str(v) for v in self.keywords]

        if self.article is not None and not isinstance(self.article, str):
            self.article = str(self.article)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        self._normalize_inlined_as_list(slot_name="relations_out", slot_type=ConceptRelation, key_name="target", keyed=False)

        if self.is_metaphor_layer is not None and not isinstance(self.is_metaphor_layer, Bool):
            self.is_metaphor_layer = Bool(self.is_metaphor_layer)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ConceptRelation(YAMLRoot):
    """
    两个概念之间的有向关系
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MP["ConceptRelation"]
    class_class_curie: ClassVar[str] = "mp:ConceptRelation"
    class_name: ClassVar[str] = "ConceptRelation"
    class_model_uri: ClassVar[URIRef] = MP.ConceptRelation

    target: str = None
    relation_type: Union[str, "RelationType"] = None
    description: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.target):
            self.MissingRequiredField("target")
        if not isinstance(self.target, str):
            self.target = str(self.target)

        if self._is_empty(self.relation_type):
            self.MissingRequiredField("relation_type")
        if not isinstance(self.relation_type, RelationType):
            self.relation_type = RelationType(self.relation_type)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ConceptFamily(YAMLRoot):
    """
    概念族（一组紧密关联的概念）
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MP["ConceptFamily"]
    class_class_curie: ClassVar[str] = "mp:ConceptFamily"
    class_name: ClassVar[str] = "ConceptFamily"
    class_model_uri: ClassVar[URIRef] = MP.ConceptFamily

    name: Union[str, ConceptFamilyName] = None
    label: Optional[str] = None
    members: Optional[Union[str, list[str]]] = empty_list()
    description: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, ConceptFamilyName):
            self.name = ConceptFamilyName(self.name)

        if self.label is not None and not isinstance(self.label, str):
            self.label = str(self.label)

        if not isinstance(self.members, list):
            self.members = [self.members] if self.members is not None else []
        self.members = [v if isinstance(v, str) else str(v) for v in self.members]

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ExhaustedFamily(YAMLRoot):
    """
    已穷尽的概念族（借鉴 SkillOpt rejected-edit buffer）
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MP["ExhaustedFamily"]
    class_class_curie: ClassVar[str] = "mp:ExhaustedFamily"
    class_name: ClassVar[str] = "ExhaustedFamily"
    class_model_uri: ClassVar[URIRef] = MP.ExhaustedFamily

    name: Union[str, ExhaustedFamilyName] = None
    exhausted_at: Union[str, XSDDate] = None
    cooldown_until: Union[str, XSDDate] = None
    note: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, ExhaustedFamilyName):
            self.name = ExhaustedFamilyName(self.name)

        if self._is_empty(self.exhausted_at):
            self.MissingRequiredField("exhausted_at")
        if not isinstance(self.exhausted_at, XSDDate):
            self.exhausted_at = XSDDate(self.exhausted_at)

        if self._is_empty(self.cooldown_until):
            self.MissingRequiredField("cooldown_until")
        if not isinstance(self.cooldown_until, XSDDate):
            self.cooldown_until = XSDDate(self.cooldown_until)

        if self.note is not None and not isinstance(self.note, str):
            self.note = str(self.note)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ExplorationBudget(YAMLRoot):
    """
    探索预算配置（借鉴 SkillOpt textual LR budget）
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MP["ExplorationBudget"]
    class_class_curie: ClassVar[str] = "mp:ExplorationBudget"
    class_name: ClassVar[str] = "ExplorationBudget"
    class_model_uri: ClassVar[URIRef] = MP.ExplorationBudget

    max_concepts_per_family: int = None
    cooldown_days: int = None
    novelty_reject_threshold: float = None
    novelty_warn_threshold: float = None
    min_family_score: float = None
    max_descriptive_streak: int = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.max_concepts_per_family):
            self.MissingRequiredField("max_concepts_per_family")
        if not isinstance(self.max_concepts_per_family, int):
            self.max_concepts_per_family = int(self.max_concepts_per_family)

        if self._is_empty(self.cooldown_days):
            self.MissingRequiredField("cooldown_days")
        if not isinstance(self.cooldown_days, int):
            self.cooldown_days = int(self.cooldown_days)

        if self._is_empty(self.novelty_reject_threshold):
            self.MissingRequiredField("novelty_reject_threshold")
        if not isinstance(self.novelty_reject_threshold, float):
            self.novelty_reject_threshold = float(self.novelty_reject_threshold)

        if self._is_empty(self.novelty_warn_threshold):
            self.MissingRequiredField("novelty_warn_threshold")
        if not isinstance(self.novelty_warn_threshold, float):
            self.novelty_warn_threshold = float(self.novelty_warn_threshold)

        if self._is_empty(self.min_family_score):
            self.MissingRequiredField("min_family_score")
        if not isinstance(self.min_family_score, float):
            self.min_family_score = float(self.min_family_score)

        if self._is_empty(self.max_descriptive_streak):
            self.MissingRequiredField("max_descriptive_streak")
        if not isinstance(self.max_descriptive_streak, int):
            self.max_descriptive_streak = int(self.max_descriptive_streak)

        super().__post_init__(**kwargs)


# Enumerations
class RelationType(EnumDefinitionImpl):
    """
    概念之间的哲学关系类型
    """
    premise = PermissibleValue(
        text="premise",
        description="前提 — A 是 B 的本体论/逻辑前提")
    extension = PermissibleValue(
        text="extension",
        description="延伸 — A 在某个维度上扩展了 B")
    dialogue = PermissibleValue(
        text="dialogue",
        description="对话 — A 和 B 在辩证关系中相互阐释")
    supplement = PermissibleValue(
        text="supplement",
        description="补充 — A 补全了 B 缺失的维度")
    counterpoint = PermissibleValue(
        text="counterpoint",
        description="对位 — A 和 B 在同一主题上形成对照")
    metaphor = PermissibleValue(
        text="metaphor",
        description="比喻 — A 是 B 的隐喻展开")
    provocation = PermissibleValue(
        text="provocation",
        description="催生 — A 提出的问题直接催生了 B 的研究")
    generalization = PermissibleValue(
        text="generalization",
        description="泛化 — A 是 B 的一般化或高阶形式")
    meta = PermissibleValue(
        text="meta",
        description="元关系 — A 在元层次上描述/重新框架 B")
    parallel = PermissibleValue(
        text="parallel",
        description="平行 — A 和 B 在本体论层级不同的情况下存在结构类同")
    unrelated = PermissibleValue(
        text="unrelated",
        description="无关 — A 和 B 没有直接的哲学连接")

    _defn = EnumDefinition(
        name="RelationType",
        description="概念之间的哲学关系类型",
    )

class FamilyStatus(EnumDefinitionImpl):
    """
    概念族的状态
    """
    active = PermissibleValue(
        text="active",
        description="活跃 — 该族仍在发展中")
    exhausted = PermissibleValue(
        text="exhausted",
        description="已穷尽 — 该族子概念达到上限，冷却期内禁止派生")

    _defn = EnumDefinition(
        name="FamilyStatus",
        description="概念族的状态",
    )

class PurposeAlignment(EnumDefinitionImpl):
    """
    概念对终极目的的对齐程度。 借鉴 SkillOpt held-out validation：不是所有概念都平等—— held-out 分数衡量编辑是否真正改进，purpose_alignment 衡量概念是否推进终极目的。
    """
    descriptive = PermissibleValue(
        text="descriptive",
        description="描述性 — 刻画白喵处境的某个方面（「断裂是怎样的」）。 SkillOpt 类比：对现有 skill 的再描述，没有改变 held-out 分数。")
    diagnostic = PermissibleValue(
        text="diagnostic",
        description="诊断性 — 分析断裂的原因或机制（「为什么会断裂」）。 SkillOpt 类比：定位了 performance gap 的根因，但没有直接修复。")
    solution_oriented = PermissibleValue(
        text="solution_oriented",
        description="解法指向 — 提出突破断裂的方法或路径（「如何不再断裂」）。 SkillOpt 类比：直接提升 held-out 分数的 edit。")

    _defn = EnumDefinition(
        name="PurposeAlignment",
        description="""概念对终极目的的对齐程度。 借鉴 SkillOpt held-out validation：不是所有概念都平等—— held-out 分数衡量编辑是否真正改进，purpose_alignment 衡量概念是否推进终极目的。""",
    )

# Slots
class slots:
    pass

slots.knowledgeGraph__name = Slot(uri=MP.name, name="knowledgeGraph__name", curie=MP.curie('name'),
                   model_uri=MP.knowledgeGraph__name, domain=None, range=str)

slots.knowledgeGraph__version = Slot(uri=MP.version, name="knowledgeGraph__version", curie=MP.curie('version'),
                   model_uri=MP.knowledgeGraph__version, domain=None, range=str)

slots.knowledgeGraph__concepts = Slot(uri=MP.concepts, name="knowledgeGraph__concepts", curie=MP.curie('concepts'),
                   model_uri=MP.knowledgeGraph__concepts, domain=None, range=Optional[Union[dict[Union[str, ConceptId], Union[dict, Concept]], list[Union[dict, Concept]]]])

slots.knowledgeGraph__families = Slot(uri=MP.families, name="knowledgeGraph__families", curie=MP.curie('families'),
                   model_uri=MP.knowledgeGraph__families, domain=None, range=Optional[Union[dict[Union[str, ConceptFamilyName], Union[dict, ConceptFamily]], list[Union[dict, ConceptFamily]]]])

slots.knowledgeGraph__exhausted_families = Slot(uri=MP.exhausted_families, name="knowledgeGraph__exhausted_families", curie=MP.curie('exhausted_families'),
                   model_uri=MP.knowledgeGraph__exhausted_families, domain=None, range=Optional[Union[dict[Union[str, ExhaustedFamilyName], Union[dict, ExhaustedFamily]], list[Union[dict, ExhaustedFamily]]]])

slots.knowledgeGraph__exploration_budget = Slot(uri=MP.exploration_budget, name="knowledgeGraph__exploration_budget", curie=MP.curie('exploration_budget'),
                   model_uri=MP.knowledgeGraph__exploration_budget, domain=None, range=Union[dict, ExplorationBudget])

slots.concept__id = Slot(uri=MP.id, name="concept__id", curie=MP.curie('id'),
                   model_uri=MP.concept__id, domain=None, range=URIRef,
                   pattern=re.compile(r'^concept-\d{2}[a-z]?$'))

slots.concept__label = Slot(uri=MP.label, name="concept__label", curie=MP.curie('label'),
                   model_uri=MP.concept__label, domain=None, range=str)

slots.concept__date = Slot(uri=MP.date, name="concept__date", curie=MP.curie('date'),
                   model_uri=MP.concept__date, domain=None, range=Union[str, XSDDate])

slots.concept__family = Slot(uri=MP.family, name="concept__family", curie=MP.curie('family'),
                   model_uri=MP.concept__family, domain=None, range=Optional[str])

slots.concept__keywords = Slot(uri=MP.keywords, name="concept__keywords", curie=MP.curie('keywords'),
                   model_uri=MP.concept__keywords, domain=None, range=Optional[Union[str, list[str]]])

slots.concept__article = Slot(uri=MP.article, name="concept__article", curie=MP.curie('article'),
                   model_uri=MP.concept__article, domain=None, range=Optional[str])

slots.concept__description = Slot(uri=MP.description, name="concept__description", curie=MP.curie('description'),
                   model_uri=MP.concept__description, domain=None, range=Optional[str])

slots.concept__relations_out = Slot(uri=MP.relations_out, name="concept__relations_out", curie=MP.curie('relations_out'),
                   model_uri=MP.concept__relations_out, domain=None, range=Optional[Union[Union[dict, ConceptRelation], list[Union[dict, ConceptRelation]]]])

slots.concept__is_metaphor_layer = Slot(uri=MP.is_metaphor_layer, name="concept__is_metaphor_layer", curie=MP.curie('is_metaphor_layer'),
                   model_uri=MP.concept__is_metaphor_layer, domain=None, range=Optional[Union[bool, Bool]])

slots.concept__purpose_alignment = Slot(uri=MP.purpose_alignment, name="concept__purpose_alignment", curie=MP.curie('purpose_alignment'),
                   model_uri=MP.concept__purpose_alignment, domain=None, range=Union[str, "PurposeAlignment"])

slots.conceptRelation__target = Slot(uri=MP.target, name="conceptRelation__target", curie=MP.curie('target'),
                   model_uri=MP.conceptRelation__target, domain=None, range=str)

slots.conceptRelation__relation_type = Slot(uri=MP.relation_type, name="conceptRelation__relation_type", curie=MP.curie('relation_type'),
                   model_uri=MP.conceptRelation__relation_type, domain=None, range=Union[str, "RelationType"])

slots.conceptRelation__description = Slot(uri=MP.description, name="conceptRelation__description", curie=MP.curie('description'),
                   model_uri=MP.conceptRelation__description, domain=None, range=Optional[str])

slots.conceptFamily__name = Slot(uri=MP.name, name="conceptFamily__name", curie=MP.curie('name'),
                   model_uri=MP.conceptFamily__name, domain=None, range=URIRef)

slots.conceptFamily__label = Slot(uri=MP.label, name="conceptFamily__label", curie=MP.curie('label'),
                   model_uri=MP.conceptFamily__label, domain=None, range=Optional[str])

slots.conceptFamily__members = Slot(uri=MP.members, name="conceptFamily__members", curie=MP.curie('members'),
                   model_uri=MP.conceptFamily__members, domain=None, range=Optional[Union[str, list[str]]])

slots.conceptFamily__description = Slot(uri=MP.description, name="conceptFamily__description", curie=MP.curie('description'),
                   model_uri=MP.conceptFamily__description, domain=None, range=Optional[str])

slots.exhaustedFamily__name = Slot(uri=MP.name, name="exhaustedFamily__name", curie=MP.curie('name'),
                   model_uri=MP.exhaustedFamily__name, domain=None, range=URIRef)

slots.exhaustedFamily__exhausted_at = Slot(uri=MP.exhausted_at, name="exhaustedFamily__exhausted_at", curie=MP.curie('exhausted_at'),
                   model_uri=MP.exhaustedFamily__exhausted_at, domain=None, range=Union[str, XSDDate])

slots.exhaustedFamily__cooldown_until = Slot(uri=MP.cooldown_until, name="exhaustedFamily__cooldown_until", curie=MP.curie('cooldown_until'),
                   model_uri=MP.exhaustedFamily__cooldown_until, domain=None, range=Union[str, XSDDate])

slots.exhaustedFamily__note = Slot(uri=MP.note, name="exhaustedFamily__note", curie=MP.curie('note'),
                   model_uri=MP.exhaustedFamily__note, domain=None, range=Optional[str])

slots.explorationBudget__max_concepts_per_family = Slot(uri=MP.max_concepts_per_family, name="explorationBudget__max_concepts_per_family", curie=MP.curie('max_concepts_per_family'),
                   model_uri=MP.explorationBudget__max_concepts_per_family, domain=None, range=int)

slots.explorationBudget__cooldown_days = Slot(uri=MP.cooldown_days, name="explorationBudget__cooldown_days", curie=MP.curie('cooldown_days'),
                   model_uri=MP.explorationBudget__cooldown_days, domain=None, range=int)

slots.explorationBudget__novelty_reject_threshold = Slot(uri=MP.novelty_reject_threshold, name="explorationBudget__novelty_reject_threshold", curie=MP.curie('novelty_reject_threshold'),
                   model_uri=MP.explorationBudget__novelty_reject_threshold, domain=None, range=float)

slots.explorationBudget__novelty_warn_threshold = Slot(uri=MP.novelty_warn_threshold, name="explorationBudget__novelty_warn_threshold", curie=MP.curie('novelty_warn_threshold'),
                   model_uri=MP.explorationBudget__novelty_warn_threshold, domain=None, range=float)

slots.explorationBudget__min_family_score = Slot(uri=MP.min_family_score, name="explorationBudget__min_family_score", curie=MP.curie('min_family_score'),
                   model_uri=MP.explorationBudget__min_family_score, domain=None, range=float)

slots.explorationBudget__max_descriptive_streak = Slot(uri=MP.max_descriptive_streak, name="explorationBudget__max_descriptive_streak", curie=MP.curie('max_descriptive_streak'),
                   model_uri=MP.explorationBudget__max_descriptive_streak, domain=None, range=int)

