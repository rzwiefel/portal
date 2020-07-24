(ns portal.chrome-extension
  (:require [portal.core :as portal]
            [portal.async :as a]
            [portal.runtime :as rt]
            [clojure.datafy :refer [datafy nav]]))

(defn send-tap! [msg]
  (js/Promise.
   (fn [resolve reject]
     (let [f (get rt/ops (:op msg))]
       (f msg resolve)))))

(defn send! [data msg]
  (js/Promise.resolve
   (case (:op msg)
     :portal.rpc/clear-values nil
     :portal.rpc/load-state
     {:portal/complete? true
      :portal/value data}
     :portal.rpc/on-nav
     (a/let [res (apply nav (:args msg))]
       {:value (datafy res)}))))

(defn reload! [] (portal/reload!))

(defn main! []
  (try
    (comment
      (js/setTimeout
       #(when (fn? js/cljs.core.add_tap)
          (js/console.log "is cljs")
          (js/cljs.core.add_tap #'rt/update-value)
          (set! js/document.body.innerHTML "<div id=\"root\"></div>")
          (portal/main! (portal/get-actions send-tap!)))
       1000))

    (let [json (js->clj (js/JSON.parse js/window.document.body.innerText)
                        :keywordize-keys true)]
      (set! js/document.body.style.margin "0")
      (set! js/document.body.innerHTML "<div id=\"root\"></div>")
      (portal/main! (portal/get-actions (partial send! json))))
    (catch js/Error e)))
