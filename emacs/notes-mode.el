(defvar notes-mode-hook nil)

(add-to-list 'auto-mode-alist
	     '("\\.notes\\'" . notes-mode))

(require 'comint)
(defun sync-notes ()
  "Syncs notes"
  (interactive)
  (save-some-buffers)
  (apply 'make-comint 
	 "notes-upload" 
	 "sync_notes"
	 nil 
	 (list (buffer-file-name)))
  (delete-other-windows)
  (switch-to-buffer-other-window "*notes-upload*"))
    
    
(defun notes-mode ()
  "Major mode for writing notes."
  (setq major-mode 'notes-mode)
  (setq mode-name "Notes")
  (run-hooks 'notes-mode-hook))

(provide 'notes-mode)
