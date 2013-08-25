import pygtk
pygtk.require('2.0')
import gtk
import gobject

def cb_changed(combo, path_string, new_iter):
    print combo, path_string, new_iter
    print combo.get_property('model').get_value(new_iter, 0)

w = gtk.Window()

#list store for cell renderer
m = gtk.ListStore(str)
for x in range(1, 5):
    m.append(["selection %d" % x])

#list store for treeview
s = gtk.ListStore(str, gobject.TYPE_OBJECT)
s.append(("hello", m))
s.append(("world", m))

cb = gtk.CellRendererCombo()

cb.set_property("model",m)
cb.set_property('text-column', 0)
cb.set_property('editable', True)
cb.set_property('has-entry', False)
cb.connect('changed', cb_changed)

c = gtk.TreeViewColumn("Test", cb)
c.set_attributes(cb, text = 0)

t = gtk.TreeView()
t.append_column(c)
t.set_model(s)

w.add(t)
w.show_all()
gtk.main()