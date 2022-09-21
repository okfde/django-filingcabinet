# Generated by Django 4.0.7 on 2022-09-20 18:28

from django.db import migrations
from django.db.models import F

from treebeard.numconv import NumConv

STEPLEN = 4
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class MP_AddHandler:
    def __init__(self):
        self.stmts = []


NUM = NumConv(len(ALPHABET), ALPHABET)


def _int2str(num):
    return NUM.int2str(num)


def _str2int(num):
    return NUM.str2int(num)


def _get_basepath(path, depth):
    """:returns: The base path of another path up to a given depth"""
    if path:
        return path[0 : depth * STEPLEN]
    return ""


def _get_path(path, depth, newstep):
    """
    Builds a path given some values
    :param path: the base path
    :param depth: the depth of the  node
    :param newstep: the value (integer) of the new step
    """
    parentpath = _get_basepath(path, depth - 1)
    key = _int2str(newstep)
    return "{0}{1}{2}".format(parentpath, ALPHABET[0] * (STEPLEN - len(key)), key)


def _inc_path(obj):
    """:returns: The path of the next sibling of a given node path."""
    newpos = _str2int(obj.path[-STEPLEN:]) + 1
    key = _int2str(newpos)
    if len(key) > STEPLEN:
        raise Exception("Path Overflow from: '%s'" % (obj.path,))
    return "{0}{1}{2}".format(
        obj.path[:-STEPLEN], ALPHABET[0] * (STEPLEN - len(key)), key
    )


class MP_AddRootHandler(MP_AddHandler):
    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs = kwargs

    def process(self):

        # do we have a root node already?
        last_root = self.kwargs["last_root"]

        if last_root:
            # adding the new root node as the last one
            newpath = _inc_path(last_root)
        else:
            # adding the first root node
            newpath = _get_path(None, 1, 1)

        newobj = self.kwargs["instance"]

        newobj.depth = 1
        newobj.path = newpath
        # saving the instance before returning it
        newobj.save()
        return newobj


class MP_AddChildHandler(MP_AddHandler):
    def __init__(self, node, model, **kwargs):
        super().__init__()
        self.node = node
        self.node_cls = node.__class__
        self.kwargs = kwargs
        self.model = model

    def process(self):
        newobj = self.kwargs["instance"]
        newobj.depth = self.node.depth + 1
        if self.node.numchild == 0:
            # the node had no children, adding the first child
            newobj.path = _get_path(self.node.path, newobj.depth, 1)
            max_length = self.node_cls._meta.get_field("path").max_length
            if len(newobj.path) > max_length:
                raise Exception(
                    "The new node is too deep in the tree, try"
                    " increasing the path.max_length property"
                    " and UPDATE your database"
                )
        else:
            # adding the new child as the last one
            newobj.path = _inc_path(self.node.last_child)
        # saving the instance before returning it
        newobj.save()
        newobj._cached_parent_obj = self.node
        self.model.objects.filter(path=self.node.path).update(
            numchild=F("numchild") + 1
        )

        # we increase the numchild value of the object in memory
        self.node.numchild += 1
        return newobj


def move_to_mp(apps, schema_editor):
    CollectionDirectory = apps.get_model("filingcabinet", "CollectionDirectory")

    directories = CollectionDirectory.objects.order_by(
        "collection_id", "tree_id", "level", "lft"
    )
    last_root = None
    cache = {}

    while len(directories) > 0:
        deferred = []
        print(len(directories))
        for node in directories:
            print(node.name, node.id, node.parent_id)
            if not node.parent_id:
                handler = MP_AddRootHandler(instance=node, last_root=last_root)
                handler.process()
                last_root = node
                node.last_child = None

            else:
                if node.parent_id not in cache:
                    deferred.append(node)
                    continue
                parent = cache[node.parent_id]
                handler = MP_AddChildHandler(parent, CollectionDirectory, instance=node)
                handler.process()
                parent.last_child = node

            cache[node.pk] = node
        directories = deferred


class Migration(migrations.Migration):

    dependencies = [
        ("filingcabinet", "0025_collectiondirectory_depth_and_more"),
    ]

    operations = [
        migrations.RunPython(move_to_mp),
    ]
