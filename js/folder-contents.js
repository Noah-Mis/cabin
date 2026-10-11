// folder-contents.js — what appears when the folder on the sill is opened.
// The folder calls these two functions:
//
//   open({ close })  once the folder has finished opening. Shows the pop-up;
//                    the pop-up calls close() on its X, Escape, or a click
//                    outside, which starts the folder closing.
//   close()          when the folder starts closing. Hides the pop-up.
//
// The pop-up itself is js/folder-popup.js; its words are in
// content/folder_content.json.
// Exports: folderContents = { open, close }

import { createFolderPopup } from './folder-popup.js';

const popup = createFolderPopup(document.getElementById('scene'), {
  bottomInset: () => document.getElementById('terminal').offsetHeight,
});

export const folderContents = {
  open({ close }) { popup.show(close); },
  close() { popup.hide(); },
};
