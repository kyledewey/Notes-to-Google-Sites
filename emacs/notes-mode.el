(defvar notes-mode-hook nil)
(defvar notes-mode-map () "")

(defun notes-mode-commands (map)
  (define-key map "\177" 'backward-delete-char-untabify))

(if notes-mode-map
    ()
  (setq notes-mode-map (make-sparse-keymap))
  (notes-mode-commands notes-mode-map))

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
    
    
(define-derived-mode notes-mode fundamental-mode "Notes"
  "Major mode for writing nodes"
  (setq major-mode 'notes-mode)
  (setq mode-name "Notes")
  (setq indent-tabs-mode nil)
  (setq tab-width 4)
  (setq indent-line-function 'insert-tab)
  (use-local-map notes-mode-map)
  (run-hooks 'notes-mode-hook))

(provide 'notes-mode)
