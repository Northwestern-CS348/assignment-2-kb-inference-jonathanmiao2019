import read, copy
from util import *
from logical_classes import *

verbose = 0

class KnowledgeBase(object):
    def __init__(self, facts=[], rules=[]):
        self.facts = facts
        self.rules = rules
        self.ie = InferenceEngine()

    def __repr__(self):
        return 'KnowledgeBase({!r}, {!r})'.format(self.facts, self.rules)

    def __str__(self):
        string = "Knowledge Base: \n"
        string += "\n".join((str(fact) for fact in self.facts)) + "\n"
        string += "\n".join((str(rule) for rule in self.rules))
        return string

    def _get_fact(self, fact):
        """INTERNAL USE ONLY
        Get the fact in the KB that is the same as the fact argument

        Args:
            fact (Fact): Fact we're searching for

        Returns:
            Fact: matching fact
        """
        for kbfact in self.facts:
            if fact == kbfact:
                return kbfact

    def _get_rule(self, rule):
        """INTERNAL USE ONLY
        Get the rule in the KB that is the same as the rule argument

        Args:
            rule (Rule): Rule we're searching for

        Returns:
            Rule: matching rule
        """
        for kbrule in self.rules:
            if rule == kbrule:
                return kbrule

    def kb_add(self, fact_rule):
        """Add a fact or rule to the KB
        Args:
            fact_rule (Fact|Rule) - the fact or rule to be added
        Returns:
            None
        """
        printv("Adding {!r}", 1, verbose, [fact_rule])
        if isinstance(fact_rule, Fact):
            if fact_rule not in self.facts:
                self.facts.append(fact_rule)
                for rule in self.rules:
                    self.ie.fc_infer(fact_rule, rule, self)
            else:
                if fact_rule.supported_by:
                    ind = self.facts.index(fact_rule)
                    for f in fact_rule.supported_by:
                        self.facts[ind].supported_by.append(f)
                else:
                    ind = self.facts.index(fact_rule)
                    self.facts[ind].asserted = True
        elif isinstance(fact_rule, Rule):
            if fact_rule not in self.rules:
                self.rules.append(fact_rule)
                for fact in self.facts:
                    self.ie.fc_infer(fact, fact_rule, self)
            else:
                if fact_rule.supported_by:
                    ind = self.rules.index(fact_rule)
                    for f in fact_rule.supported_by:
                        self.rules[ind].supported_by.append(f)
                else:
                    ind = self.rules.index(fact_rule)
                    self.rules[ind].asserted = True

    def kb_assert(self, fact_rule):
        """Assert a fact or rule into the KB

        Args:
            fact_rule (Fact or Rule): Fact or Rule we're asserting
        """
        printv("Asserting {!r}", 0, verbose, [fact_rule])
        self.kb_add(fact_rule)

    def kb_ask(self, fact):
        """Ask if a fact is in the KB

        Args:
            fact (Fact) - Statement to be asked (will be converted into a Fact)

        Returns:
            listof Bindings|False - list of Bindings if result found, False otherwise
        """
        print("Asking {!r}".format(fact))
        if factq(fact):
            f = Fact(fact.statement)
            bindings_lst = ListOfBindings()
            # ask matched facts
            for fact in self.facts:
                binding = match(f.statement, fact.statement)
                if binding:
                    bindings_lst.add_bindings(binding, [fact])

            return bindings_lst if bindings_lst.list_of_bindings else []

        else:
            print("Invalid ask:", fact.statement)
            return []
    def kb_remove(self, fr):
        if not self.kb_supported(fr):
            # Remove it's support from all facts and rules
            for instance in fr.supports_rules:
                instance.supported_by.remove(fr)
                self.kb_remove(instance)
            for instance in fr.supports_facts:
                instance.supported_by.remove(fr)
                self.kb_remove(instance)

            if isinstance(fr, Fact):
                self.facts.remove(fr)
            if isinstance(fr, Rule):
                self.rules.remove(fr)

    def kb_supported(self, fact):
        if len(fact.supported_by) > 1:
            return True
        else:
            return False

    def kb_retract(self, fact):
        """Retract a fact from the KB

        Args:
            fact (Fact) - Fact to be retracted

        Returns:
            None
        """
        printv("Retracting {!r}", 0, verbose, [fact])
        ####################################################
        # Student code goes here
        # First check that we are retracting a fact that exists in the database
        if isinstance(fact, Fact) and self.kb_ask(fact):
            kb_fact = self._get_fact(fact)
            # if asserted and supported, change asserted to false
            if self.kb_supported(kb_fact) and kb_fact.asserted:
                kb_fact.asserted = False
            # if not asserted but supported, do nothing
            elif not kb_fact.asserted and self.kb_supported(kb_fact):
                return
            # if not supported, remove
            elif not self.kb_supported(kb_fact):
                self.kb_remove(kb_fact)


class InferenceEngine(object):
    def fc_infer(self, fact, rule, kb):
        """Forward-chaining to infer new facts and rules

        Args:
            fact (Fact) - A fact from the KnowledgeBase
            rule (Rule) - A rule from the KnowledgeBase
            kb (KnowledgeBase) - A KnowledgeBase

        Returns:
            Nothing            
        """
        printv('Attempting to infer from {!r} and {!r} => {!r}', 1, verbose,
            [fact.statement, rule.lhs, rule.rhs])
        ####################################################
        # Student code goes here
        bindings = match(fact.statement, rule.lhs[0])
        new_lhs = []
        length = 0
        if bindings:
            length = len(rule.lhs)

        # if it is a match, rhs of rule is
        if bindings:
            if length is 1:
                new_statement = instantiate(rule.rhs, bindings)
                new_fr = Fact(new_statement, [fact, rule])
                fact.supports_facts.append(new_fr)
                rule.supports_facts.append(new_fr)
                kb.kb_add(new_fr)
            else:
                for i in range(1, length):
                    new_statement = instantiate(rule.lhs[i], bindings)
                    new_lhs.append(new_statement)
                new_rhs = instantiate(rule.rhs, bindings)
                new_fr = Rule([new_lhs, new_rhs], [fact, rule])

                fact.supports_rules.append(new_fr)
                rule.supports_rules.append(new_fr)
                kb.kb_add(new_fr)
