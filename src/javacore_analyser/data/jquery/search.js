/*
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
*/

$(function() {

  // the input field
  var $input = $("input[type='search']"),
    // search button
    $searchBtn = $("button[data-search='search']"),
    // clear button
    $clearBtn = $("button[data-search='clear']"),
    // prev button
    $prevBtn = $("button[data-search='prev']"),
    // next button
    $nextBtn = $("button[data-search='next']"),
    // the context where to search
    $content = $(".content"),
    // jQuery object to save <mark> elements
    $results,
    // the class that will be appended to the current
    // focused element
    currentClass = "current",
    // top offset for the jump (the search bar)
    offsetTop = 50,
    // the current index of the focused element
    currentIndex = 0;

  /**
   * Jumps to the element matching the currentIndex
   */
  function jumpTo() {
    if ($results.length) {
      var position,
        $current = $results.eq(currentIndex);
      $results.removeClass(currentClass);
      if ($current.length) {
        $current.addClass(currentClass);
        position = $current.offset().top - offsetTop;
        window.scrollTo(0, position - 100);
      }
    }
  }

  function search(searchTerm) {
    console.log("searching for " + searchTerm);
    rootNode = document.getElementById('doc_body');
    searchInNode(rootNode, searchTerm);
  }

    function processChild(child) {
        try {
            if (isDomNode(child) && child.classList.contains('toggle_expand')) {
                for (i = 0; i < child.childNodes.length; ++i) {
                    grandchild = child.childNodes[i];
                    if (isDomNode(grandchild) && grandchild.text == '[+] Expand') {
                        grandchild.text = '[-] Collapse';
                    }
                }
            }
        } catch(err) {
            console.log(err);
        }
    }

    function searchInNode(node, searchTerm) {
        if (!isDomNode(node)) return;
        if (node.textContent.toUpperCase().match(searchTerm.toUpperCase())) {
            // expand the node here
            if (!node.classList.contains('show-all')) {
                node.classList.add('show-all');
                for (i = 0; i < node.childNodes.length; ++i) {
                    child = node.childNodes[i];
                    processChild(child);
                }
            }
            if (node.getAttribute('style') && node.style.display == "none") {
                node.style.display = "";
            }
        }
        for (var i = 0; i < node.childNodes.length; ++i) {
            searchInNode(node.childNodes[i], searchTerm);
        }
    }

    function isDomNode(node) {
        return (
            typeof HTMLElement === "object" ?
                node instanceof HTMLElement :
                node && typeof node === "object" && node !== null && node.nodeType === 1 && typeof node.nodeName==="string"
        );
    }

  /**
   * Searches for the entered keyword in the
   * specified context on input
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
    searchTerm = document.getElementById('search-input').value
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
