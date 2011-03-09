#!/usr/bin/env python

# BlogPost - An simple Blog publisher
#
# Copyright (C) 2009 Suresh Jayaraman <sureshjayaram@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# If you find any bugs or have any suggestions email me.

# File:	BlogPost.py

# Supress known deprecation warning about use of sha module
import warnings
def supress_warnings():
	warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings():
	warnings.simplefilter("ignore", DeprecationWarning)
	from gdata import service
	import gdata.blogger.service
	import gdata
	import atom
	supress_warnings()

import pygtk
pygtk.require('2.0')
import gtk
from user import home
import cPickle
import os
import xml.dom.ext
import xml.dom.minidom


BLOGPOST_USER_DIR = home + "/.BlogPost"
BLOGPOST_DRAFTS_DIR = BLOGPOST_USER_DIR + "/drafts"
CRED_FILE = BLOGPOST_USER_DIR + "/.cred"
LABEL_SCHEME = "http://www.blogger.com/atom/ns#"

class BlogPost:

	def query_blog(self, blogger):
		query = service.Query()
		query.feed = '/feeds/default/blogs'
		try:
			self.feed = blogger.Get(query.ToUri())
		except gdata.service.Error:
			self.show_error("Error: Unable to get Blog names")
			main.gtk.quit()

		for entry in self.feed.entry:
			self.blognames.append(entry.title.text)

		self.blogid = self.feed.entry[0].GetSelfLink().href.split("/")[-1]
		return self.blogid

	def authenticate(self, login, passwd):
		svc = service.GDataService(login, passwd)
		svc.source = 'BlogPost-0.1'
		svc.service = 'blogger'
		svc.account_type = 'GOOGLE'
		svc.server = 'www.blogger.com'
		try:
			svc.ProgrammaticLogin()
		except gdata.service.BadAuthentication:
			self.show_status("Incorrect Username/Password")
			main.gtk.quit()
		except gdata.service.Error:
			self.show_status("Login Error. Please check account settings")
			main.gtk.quit()

		return svc

	def publish_entry(self, widget):
		title = self.titleentry.get_text()

		start = self.buffer.get_start_iter()
		end = self.buffer.get_end_iter()
		contents = self.buffer.get_text(start, end)

		entry = gdata.GDataEntry()
		entry.title = atom.Title('xhtml', title)
		entry.content = atom.Content(content_type='html', text=contents)
		tags = self.tagsentry.get_text()
		entry.category = atom.Category(scheme=LABEL_SCHEME, term=tags)

		try:
			self.blogger.Post(entry, '/feeds/%s/posts/default/' % self.blogid)
		except gdata.service.Error:
			self.show_error("Error: Unable to post entry")

		self.show_status("Entry successfully posted!")
		self.on_NewEntry(self)

	def get_iters(self):

		start = None
		end = None

		if (not self.buffer):
			self.show_error("Error: Text not selected")
			return start, end

		bounds = self.buffer.get_selection_bounds()
		if (bounds):
			start, end = bounds
		else:
			cursor = self.buffer.get_insert()
			start = self.buffer.get_iter_at_mark(cursor)
			end = self.buffer.get_iter_at_mark(cursor)

		return start, end

	def iterator_warning(self):
		warnings.warn("ignore", gtk.Warning)

	def wrap_selected(self, tagstart, tagend):

		start, end = self.get_iters()
		if ((not start) or (not end)):
			self.show_error("Error: Error occured while formatting text")
			return
		start_mark = self.buffer.create_mark(None, start, True)
		end_mark = self.buffer.create_mark(None, end, False)

		self.buffer.insert(start, tagstart)
		end = self.buffer.get_iter_at_mark(end_mark)
		self.buffer.insert(end, tagend)

		# Handle harmless invalid iterator warning
		with warnings.catch_warnings():
			warnings.simplefilter("ignore", gtk.Warning)
		
			self.buffer.select_range(end, start)
			self.iterator_warning()

		self.buffer.delete_mark(start_mark)
		self.buffer.delete_mark(end_mark)

	def show_status(self, statusmsg):
		msg_dlg = gtk.MessageDialog(type=gtk.MESSAGE_INFO,
					message_format=statusmsg,
					buttons=gtk.BUTTONS_OK)
		msg_dlg.run()
		msg_dlg.destroy()


	def show_error(self, error_str):
		error_dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
					message_format=error_str,
					buttons=gtk.BUTTONS_OK)
		error_dlg.run()
		error_dlg.destroy()

	def get_cred(self):
		if os.path.isfile(CRED_FILE):
			info = open(CRED_FILE, 'rb')
			try:
				self.user = cPickle.load(info)
				self.password = cPickle.load(info)
				info.close()
				return True
			except EOFError:
				self.user = ""
				self.password = ""
				info.close()
				return False

	def set_cred(self):
		savefile = open(CRED_FILE, 'wb')
		cPickle.dump(self.user, savefile)
		cPickle.dump(self.password, savefile)
		savefile.close()


	def on_DeleteEvent(self, widget, event, data=None):
		return False

	def destroy(self, widget, data=None):
		gtk.main_quit()

	def on_blogname_select(self, widget):
		self.blogindex = self.combobox.get_active()
		self.blogid = self.feed.entry[self.blogindex].GetSelfLink().href.split("/")[-1]

	def on_NewEntry(self, widget):
		self.titleentry.set_text("")
		self.buffer.set_text("")
		self.tagsentry.set_text("")

	def on_Clear(self, widget):
		self.buffer.set_text("")

	def on_ApplySettings(self, widget, window, login, passwd):
		self.user = login.get_text()
		self.password = passwd.get_text()

		if (self.user and self.password and self.save_settings):
			self.set_cred()
		window.destroy()

	def on_RememberSettings(self, widget):
		self.save_settings = widget.get_active()

	def on_CancelInit(self, widget, window):
		exit()

	def on_Cancel(self, widget, window):
		window.destroy()

	def on_BtnBold(self, widget):
		self.wrap_selected("<b>", "</b>")

	def on_BtnItalic(self, widget):
		self.wrap_selected("<i>", "</i>")

	def on_BtnUnderline(self, widget):
		self.wrap_selected("<u>", "</u>")

	def on_BtnStrike(self, widget):
		self.wrap_selected("<strike>", "</strike>")

	def on_AddLink(self, widget, window, text, url):
		if (not text):
			self.show_error(" Please enter the Text to Link.")
		if (not url):
			self.show_error("Please enter the URL to link to")
		start, end = self.get_iters()
		try:
			self.buffer.select_range(end, start)
		except GtkWarning:
			pass
		self.wrap_selected("<a href=\"%s\">%s" % (url.get_text(), text.get_text()), "</a>")
		window.destroy()

	def on_AddImage(self, widget):
		show_status("Functionality not supported, yet")

	def on_OpenDraft(self, widget):
		openfile = gtk.FileChooserDialog("Open..", None,
				gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_OPEN,
					gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
					gtk.RESPONSE_CANCEL))
		openfile.set_default_response(gtk.RESPONSE_OK)
		openfile.set_current_folder(BLOGPOST_DRAFTS_DIR)
		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		openfile.add_filter(filter)

		response = openfile.run()
		if response == gtk.RESPONSE_OK:
			dfile =  openfile.get_filename()
			
			FILE = open(dfile, "r")
			doc = xml.dom.minidom.parse(dfile)
			for node in doc.getElementsByTagName("entry"):
				titles = node.getElementsByTagName("title")
				for node1 in titles:
					for node2 in node1.childNodes:
						title = node2.data
				content = node.getElementsByTagName("desc")
				for node1 in content:
					for node2 in node1.childNodes:
						desc = node2.data
				self.titleentry.set_text(title)
				self.buffer.set_text(desc)
				
			FILE.close()	

		openfile.destroy()

	def on_SaveDraft(self, widget):
		draft = gtk.FileChooserDialog("Save..", None,
				gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_SAVE, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
		draft.set_default_response(gtk.RESPONSE_OK)
		draft.set_current_folder(BLOGPOST_DRAFTS_DIR)

		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		draft.add_filter(filter)

		response = draft.run()
		if response == gtk.RESPONSE_OK:
			file =  draft.get_filename()

			title = self.titleentry.get_text()
			start = self.buffer.get_start_iter()
			end = self.buffer.get_end_iter()
			contents = self.buffer.get_text(start, end)
			self.save_draft(file, title, contents)
			self.on_NewEntry(self)

		draft.destroy()

	def DlgAddLink(self, widget):
		dlglink = gtk.Dialog()

		table = gtk.Table(2, 2, False)
		table.set_row_spacing(0, 0)
		table.set_col_spacing(0, 0)
		txtlb = gtk.Label("Text:")
		txtlb.set_width_chars(15)
		urllb = gtk.Label("URL:")
		urllb.set_width_chars(15)
		txtent = gtk.Entry()
		urlent = gtk.Entry()
		table.attach(txtlb, 0, 1, 0, 1)
		table.attach(urllb, 0, 1, 1, 2)
		table.attach(txtent, 1, 2, 0, 1)
		table.attach(urlent, 1, 2, 1, 2)

		act = gtk.HBox(False, 0)
		applybt = gtk.Button("Apply", gtk.STOCK_APPLY)
		cancelbt = gtk.Button("Cancel", gtk.STOCK_CANCEL)
		act.add(applybt)
		act.add(cancelbt)

		applybt.connect("clicked", self.on_AddLink, dlglink, txtent, urlent)
		cancelbt.connect("clicked", self.on_Cancel, dlglink)

		dlglink.vbox.pack_start(table, True, True, 0)
		dlglink.action_area.pack_start(act, True, True, 0)

		dlglink.set_title("Create Link")	
		dlglink.show_all()

	def DlgAddImage(self, widget):
		imgfile = gtk.FileChooserDialog(title="Select Image", action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_OPEN, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)) 

		filter = gtk.FileFilter()
		filter.set_name("Images")
		filter.add_mime_type("image/png")
		filter.add_mime_type("image/jpeg")
		filter.add_mime_type("image/gif")
		filter.add_pattern("*.png")
		filter.add_pattern("*.jpg")
		filter.add_pattern("*.gif")
		imgfile.add_filter(filter)
		filter = gtk.FileFilter()
		filter.set_name("All Files")
		filter.add_pattern("")
		imgfile.add_filter(filter)

		result = ""
		if imgfile.run() == gtk.RESPONSE_OK:
			result = imgfile.get_filename()

		imgfile.destroy()	

		return result

	def save_draft(self, file, title, contents):
		doc = xml.dom.minidom.Document()
		entry = doc.createElementNS("", "entry")
		subject = doc.createElementNS("", "title")
		desc = doc.createElementNS("", "desc")
		entry.appendChild(subject)
		entry.appendChild(desc)
		titletxt=doc.createTextNode(title)
		subject.appendChild(titletxt)
		contenttxt=doc.createTextNode(contents)
		desc.appendChild(contenttxt)
		doc.appendChild(entry)
		FILE = open(file, "w")
		xml.dom.ext.PrettyPrint(doc, FILE)
		FILE.close()

	def DlgSetup(self, widget, window): 
		prefdialog = gtk.Dialog()

		table = gtk.Table(3, 2, True)
		table.set_row_spacing(0, 0)
		table.set_col_spacing(0, 0)
		serverlb = gtk.Label("Server:")
		loginlb = gtk.Label("Login:")
		passwdlb = gtk.Label("Password:")
		serverent = gtk.Entry()
		serverent.set_text("blogger.com")
		serverent.set_editable(False)
		loginent = gtk.Entry()
		passwdent = gtk.Entry()
		passwdent.set_visibility(False)

		if (os.path.isfile(CRED_FILE)):
			if self.save_settings:
				self.get_cred()
				loginent.set_text(self.user)
				passwdent.set_text(self.password)

		chkbox = gtk.CheckButton("Remember settings")
		chkbox.connect("toggled", self.on_RememberSettings)
		chkbox.set_active(True)

		actionbox = gtk.HBox(False, 0)
		applybt = gtk.Button("Apply", gtk.STOCK_APPLY)
		cancelbt = gtk.Button("Cancel", gtk.STOCK_CANCEL)
		actionbox.add(applybt)
		actionbox.add(cancelbt)
		applybt.connect("clicked", self.on_ApplySettings, prefdialog, loginent, passwdent)
		if window == "MainMenu":
			cancelbt.connect("clicked", self.on_Cancel, prefdialog)
		else:
			cancelbt.connect("clicked", self.on_CancelInit, prefdialog)


		table.attach(serverlb, 0, 1, 0, 1)
		table.attach(loginlb, 0, 1, 1, 2)
		table.attach(passwdlb, 0, 1, 2, 3)
		table.attach(serverent, 1, 2, 0, 1)
		table.attach(loginent, 1, 2, 1, 2)
		table.attach(passwdent, 1, 2, 2, 3)

		prefdialog.vbox.pack_start(table, True, True, 0)
		prefdialog.vbox.pack_start(chkbox, False, False, 0)
		prefdialog.action_area.pack_start(actionbox, True, True, 0)

		prefdialog.show_all()
		prefdialog.set_title("Setup Account")	
		prefdialog.run()

		prefdialog.destroy()


	def make_layout(self):
		vbox = gtk.VBox(False, 0)

		self.menu = gtk.MenuBar()
		
		self.filemenu = gtk.Menu()
		filem = gtk.MenuItem("BlogPost")
		filem.set_submenu(self.filemenu)
		new = gtk.ImageMenuItem(gtk.STOCK_NEW, None)
		new.connect("activate", self.on_NewEntry)
		self.filemenu.append(new)
		open = gtk.ImageMenuItem(gtk.STOCK_OPEN, None)
		open.connect("activate", self.on_OpenDraft)
		self.filemenu.append(open)
		save = gtk.ImageMenuItem(gtk.STOCK_SAVE, None)
		save.connect("activate", self.on_SaveDraft)
		self.filemenu.append(save)
		sep = gtk.SeparatorMenuItem()
		self.filemenu.append(sep)
		quit = gtk.ImageMenuItem(gtk.STOCK_QUIT, None)
		quit.connect("activate", gtk.main_quit)
		self.filemenu.append(quit)
		self.menu.append(filem)

		self.editmenu = gtk.Menu()
		edit = gtk.MenuItem("Edit")
		edit.set_submenu(self.editmenu)
		pref = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES, None)
		pref.connect("activate", self.DlgSetup, "MainMenu")
		self.editmenu.append(pref)

		self.menu.append(edit)

		self.helpmenu = gtk.Menu()
		help = gtk.MenuItem("Help")
		help.set_submenu(self.helpmenu)
		about = gtk.ImageMenuItem(gtk.STOCK_ABOUT, None)
		self.helpmenu.append(about)
		self.menu.append(help)

		vbox.pack_start(self.menu, False, False, 10)

		# Title
		self.hboxtitle = gtk.HBox(False, 0)
		label = gtk.Label("Title:")
		label.set_justify(gtk.JUSTIFY_LEFT)
		self.hboxtitle.pack_start(label, False, False, 5)
		self.titleentry = gtk.Entry()
		vbox.pack_start(self.hboxtitle, False, False, 5)
		self.hboxtitle.pack_start(self.titleentry, True, True, 5)

		# Tool bar */
		self.toolbar = gtk.Toolbar()
		self.toolbar.set_style(gtk.TOOLBAR_ICONS)
		bold = gtk.ToolButton(gtk.STOCK_BOLD)
		bold.connect("clicked", self.on_BtnBold)
		self.toolbar.insert(bold, 0)
		italic = gtk.ToolButton(gtk.STOCK_ITALIC)
		italic.connect("clicked", self.on_BtnItalic)
		self.toolbar.insert(italic, -1)
		underline = gtk.ToolButton(gtk.STOCK_UNDERLINE)
		underline.connect("clicked", self.on_BtnUnderline)
		self.toolbar.insert(underline, -1)
		strike = gtk.ToolButton(gtk.STOCK_STRIKETHROUGH)
		strike.connect("clicked", self.on_BtnStrike)
		self.toolbar.insert(strike, -1)
		sep1 = gtk.SeparatorToolItem()
		self.toolbar.insert(sep1, -1)
		linkicon = gtk.Image()
		linkicon.set_from_file("/usr/share/blogpost/pixmaps/stock_link.png")
		link = gtk.ToolButton()
		link.set_icon_widget(linkicon)
		link.set_label("Add Link")
		link.connect("clicked", self.DlgAddLink)
		self.toolbar.insert(link, -1)
		imageicon = gtk.Image()
		imageicon.set_from_file("/usr/share/blogpost/pixmaps/stock_insert_image.png")
		image = gtk.ToolButton()
		image.set_icon_widget(imageicon)
		image.set_label("Image")
		image.connect("clicked", self.on_AddImage)
		self.toolbar.insert(image, -1)
		sep2 = gtk.SeparatorToolItem()
		self.toolbar.insert(sep2, -1)
		clear = gtk.ToolButton(gtk.STOCK_CLEAR)
		clear.connect("clicked", self.on_Clear)
		self.toolbar.insert(clear, -1)
		
		vbox.pack_start(self.toolbar, False, False, 5)

		# Text editor
		self.view = gtk.TextView()
		self.buffer = self.view.get_buffer()

		self.viewscrolled = gtk.ScrolledWindow()
		self.viewscrolled.set_shadow_type(gtk.SHADOW_IN)
		self.viewscrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.viewscrolled.add(self.view)
		vbox.pack_start(self.viewscrolled, True, True, 5)

		# Tags
		self.hboxtags = gtk.HBox(False, 0)
		labeltags = gtk.Label("Tags:")
		labeltags.set_justify(gtk.JUSTIFY_LEFT)
		self.tagsentry = gtk.Entry()
		self.hboxtags.pack_start(labeltags, False, False, 5)
		self.hboxtags.pack_start(self.tagsentry, False, False, 5)

		labelselect = gtk.Label("Blog Name:")

		self.combobox = gtk.combo_box_new_text()
		if len(self.blognames) == 0:
			self.combobox.append_text('None')
		else:
			for entry in self.blognames:
				self.combobox.append_text(entry)
			self.combobox.connect("changed", self.on_blogname_select)
			self.combobox.set_active(0)

		self.hboxtags.pack_start(labelselect, False, False, 5)
		self.hboxtags.pack_start(self.combobox, True, True, 5)
		vbox.pack_start(self.hboxtags, False, False, 5)

		hboxaction = gtk.HBox(True, 0)
		savedraft = gtk.Button()
		savedraft.set_label("Save Draft")
		savedraft.set_size_request(80, 30)
		savedraft.connect("clicked", self.on_SaveDraft)
		hboxaction.add(savedraft)
		publish = gtk.Button()
		publish.set_label("Publish")
		publish.connect("clicked", self.publish_entry)
		hboxaction.add(publish)
		halign = gtk.Alignment(1, 0, 0, 0)
		halign.add(hboxaction)
		vbox.pack_start(halign, False, False, 10)

		return vbox

	def __init__(self):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.connect("delete_event", self.on_DeleteEvent)
		self.window.connect("destroy", self.destroy)
		self.window.set_default_size(400, 400)
		self.window.set_border_width(0)
		self.window.set_title("BlogPost")

		self.blognames = []
		self.save_settings = True

		if (not os.path.isdir(BLOGPOST_USER_DIR)):
			os.mkdir(BLOGPOST_USER_DIR)
		if (not os.path.isdir(BLOGPOST_DRAFTS_DIR)):
			os.mkdir(BLOGPOST_DRAFTS_DIR)

		if (not os.path.isfile(CRED_FILE)):
			self.DlgSetup(self, "Init")
		else:
			self.get_cred()

		''' XXX: Should be optimized to check whether session is valid and
		    try only if it is invalid '''
		self.blogger = self.authenticate(self.user, self.password)
		self.blogid = self.query_blog(self.blogger)

		layout = self.make_layout()
		self.window.add(layout)
	
		self.window.show_all()

	def main(self):
		gtk.main()

if __name__ == "__main__":
	post = BlogPost()
	post.main()
