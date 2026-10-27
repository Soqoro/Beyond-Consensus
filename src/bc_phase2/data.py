"""Local synthetic record boundaries; no dataset downloads or estimator fitting."""
import random
from dataclasses import dataclass
from .model import Invalid, digest, rational


def adapt(kind,row):
    if not isinstance(row,dict) or not isinstance(row.get('id'),str):raise Invalid('source problem identity')
    if kind=='math500':
        public={'id':row['id'],'problem':row['problem']};private={'answer':row.get('answer')}
    elif kind=='gpqa':
        choices=[row['Correct Answer']]+[row[f'Incorrect Answer {i}'] for i in (1,2,3)]
        order=list(range(4));random.Random(int(digest(['gpqa-choice-v1',row['id']]),16)).shuffle(order)
        public={'id':row['id'],'question':row['Question'],'choices':[choices[i] for i in order]}
        private={'answer':order.index(0),'permutation':order}
    elif kind=='gaia':
        public={'id':row['id'],'question':row['Question']};private={'answer':row.get('Final answer')}
    else:raise Invalid('adapter disabled or unresolved identity')
    # No raw extras, answer field names, tools, file paths, annotations or explanations.
    return public,private


def source_split(development,test):
    if len(set(development))!=len(development) or len(set(test))!=len(test) or set(development)&set(test):raise Invalid('source split duplicate/leakage')
    return digest([sorted(development),sorted(test)])


@dataclass(frozen=True)
class SuppliedEstimator:
    version: str
    development_sources: tuple
    weights: tuple
    unit: str = 'synthetic_work'
    def estimate(self,workflow,features=None):
        if features is not None and set(features)-{'task_type','declared_input_length'}:raise Invalid('runtime/held-out feature leakage')
        values=dict(self.weights)
        if set(values)!=set(workflow.ids):raise Invalid('unknown task type/cost: no invented fallback')
        return {t:rational(v) for t,v in values.items()}
    def validate_fit_sources(self,sources):
        if not set(sources)<=set(self.development_sources):raise Invalid('estimator may use development sources only')


def evaluate_fixture(kind,answer,private):
    """Synthetic boundary test, not an official dataset evaluator."""
    if kind not in ('math500','gpqa','gaia'):raise Invalid('unsupported synthetic evaluator')
    if private.get('answer') is None or answer is None:return {'semantic':'unknown','evaluator':'synthetic-exact-equality-v1'}
    return {'semantic':'valid' if type(answer) is type(private['answer']) and answer==private['answer'] else 'invalid',
            'evaluator':'synthetic-exact-equality-v1'}
