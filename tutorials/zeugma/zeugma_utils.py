from __future__ import print_function
from __future__ import division
from builtins import range
import codecs
import csv

from fonduer.lf_helpers import *
from fonduer.snorkel.models import GoldLabel, GoldLabelKey
from fonduer.snorkel.utils import ProgressBar


def get_gold_dict(filename,
                  doc_on=True,
                  part_on=True,
                  val_on=True,
                  attribute=None,
                  docs=None):
    with codecs.open(filename, encoding="utf-8") as csvfile:
        gold_reader = csv.reader(csvfile)
        gold_dict = set()
        for row in gold_reader:
            (doc, part, attr, val) = row
            if docs is None or doc.upper() in docs:
                if attribute and attr != attribute:
                    continue
                if not val:
                    continue
                else:
                    key = []
                    if doc_on: key.append(doc.upper())
                    if part_on: key.append(part.upper())
                    if val_on: key.append(val.upper())
                    gold_dict.add(tuple(key))
    return gold_dict


def load_hardware_labels(session,
                         candidate_class,
                         filename,
                         attrib,
                         annotator_name='gold'):

    ak = session.query(GoldLabelKey).filter(
        GoldLabelKey.name == annotator_name).first()
    if ak is None:
        ak = GoldLabelKey(name=annotator_name)
        session.add(ak)
        session.commit()

    candidates = session.query(candidate_class).all()
    gold_dict = get_gold_dict(filename, attribute=attrib)
    cand_total = len(candidates)
    print('Loading', cand_total, 'candidate labels')
    pb = ProgressBar(cand_total)
    labels = []
    for i, c in enumerate(candidates):
        pb.bar(i)
        doc = (c[0].sentence.document.name).upper()
        part = (c[0].get_span()).upper()
        val = (''.join(c[1].get_span().split())).upper()
        context_stable_ids = '~~'.join([i.stable_id for i in c.get_contexts()])
        label = session.query(GoldLabel).filter(GoldLabel.key == ak).filter(
            GoldLabel.candidate == c).first()
        if label is None:
            if (doc, part, val) in gold_dict:
                label = GoldLabel(candidate=c, key=ak, value=1)
            else:
                label = GoldLabel(candidate=c, key=ak, value=-1)
            session.add(label)
            labels.append(label)
    session.commit()
    pb.close()

    session.commit()
    print("AnnotatorLabels created: %s" % (len(labels), ))