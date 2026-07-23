/*
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
*/

// 'use strict' opts this file into strict mode: undeclared variables, duplicate
// parameter names, and other silent JavaScript mistakes become hard errors.
'use strict';

$(function() {

  // the input field
  const $input = $("input[type='search']");
  // search button
  const $searchBtn = $("button[data-search='search']");
  // clear button
  const $clearBtn = $("button[data-search='clear']");
  // prev button
  const $prevBtn = $("button[data-search='prev']");
  // next button
  const $nextBtn = $("button[data-search='next']");
  // the context where to search
  const $content = $(".content");
  // jQuery object to save <mark> elements
  let $results;
  // the class that will be appended to the current focused element
  const currentClass = "current";
  // top offset for the jump (the search bar)
  const offsetTop = 50;
  // the current index of the focused element
  let currentIndex = 0;

  /**
   * Jumps to the element matching the currentIndex
   */
  function jumpTo() {
    if ($results.length) {
      const $current = $results.eq(currentIndex);
      $results.removeClass(currentClass);
      if ($current.length) {
        $current.addClass(currentClass);
        const position = $current.offset().top - offsetTop;
        window.scrollTo(0, position - 100);
      }
    }
  }

  function search(searchTerm) {
    console.log("searching for " + searchTerm);
    const rootNode = document.getElementById('doc_body');
    searchInNode(rootNode, searchTerm);
  }

  function processChild(child) {
    try {
      if (isDomNode(child) && child.classList.contains('toggle_expand')) {
        for (let i = 0; i < child.childNodes.length; ++i) {
          const grandchild = child.childNodes[i];
          if (isDomNode(grandchild) && grandchild.text === '[+] Expand') {
            grandchild.text = '[-] Collapse';
          }
        }
      }
    } catch (err) {
      console.log(err);
    }
  }

  function searchInNode(node, searchTerm) {
    if (!isDomNode(node)) return;
    if (node.textContent.toUpperCase().match(searchTerm.toUpperCase())) {
      // expand the node here
      if (!node.classList.contains('show-all')) {
        node.classList.add('show-all');
        for (let i = 0; i < node.childNodes.length; ++i) {
          processChild(node.childNodes[i]);
        }
      }
      if (node.getAttribute('style') && node.style.display === "none") {
        node.style.display = "";
      }
    }
    for (let i = 0; i < node.childNodes.length; ++i) {
      searchInNode(node.childNodes[i], searchTerm);
    }
  }

  function isDomNode(node) {
    return (
      typeof HTMLElement === "object"
        ? node instanceof HTMLElement
        : node && typeof node === "object" && node !== null && node.nodeType === 1 && typeof node.nodeName === "string"
    );
  }

  /**
   * Searches for the entered keyword in the specified context on input
   */
  $input.on("keypress", function(event) {
    if (event.key === "Enter") {
      $searchBtn.click();
    }
  });

  function highlight(searchTerm) {
    $content.unmark({
      done: function() {
        $content.mark(searchTerm, {
          separateWordSearch: true,
          done: function() {
            $results = $content.find("mark");
            currentIndex = 0;
            jumpTo();
          }
        });
      }
    });
  }

  $searchBtn.on('click', function() {
    performSearch();
  });

  function performSearch() {
    const searchTerm = document.getElementById('search-input').value;
    search(searchTerm);
    highlight(searchTerm);
  }

  /**
   * Clears the search
   */
  $clearBtn.on("click", function() {
    $content.unmark();
    $input.val("").focus();
  });

  /**
   * Next and previous search jump to
   */
  $nextBtn.add($prevBtn).on("click", function() {
    if ($results.length) {
      currentIndex += $(this).is($prevBtn) ? -1 : 1;
      if (currentIndex < 0) {
        currentIndex = $results.length - 1;
      }
      if (currentIndex > $results.length - 1) {
        currentIndex = 0;
      }
      jumpTo();
    }
  });
});
